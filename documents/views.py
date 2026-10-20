
import logging
from pathlib import Path

from html import escape
from io import BytesIO

from django.http import FileResponse
from django.utils import timezone

from reportlab.lib import colors

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


from django.shortcuts import get_object_or_404

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from document_processing.processors import read_document
from document_processing.validators import validate_records
from .models import Document, DocumentResult


logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@api_view(["GET"])
def health_check(request):
    return Response(
        {
            "status": "healthy",
            "service": "Qveto Document Processing API",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    uploaded_file = request.FILES.get("file")

    if uploaded_file is None:
        return Response(
            {
                "message": "A file is required in the 'file' field.",
                "error_code": "FILE_REQUIRED",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    original_filename = (
        uploaded_file.name.replace("\\", "/").split("/")[-1].strip()
    )
    extension = Path(original_filename).suffix.lower()

    if not original_filename or extension not in ALLOWED_EXTENSIONS:
        return Response(
            {
                "message": "Only CSV and XLSX files are supported for invoice validation.",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size == 0:
        return Response(
            {
                "message": "The uploaded file is empty.",
                "error_code": "EMPTY_FILE",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return Response(
            {
                "message": "The maximum upload size is 10 MB.",
                "error_code": "FILE_TOO_LARGE",
            },
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    document = None

    try:
        with transaction.atomic():
            document = Document(
                original_filename=original_filename[:255],
                status=Document.Status.PROCESSING,
            )
            document.file.save(original_filename, uploaded_file, save=True)

            records = read_document(document.file.path)
            validated_records = validate_records(records)

            results = [
                DocumentResult(
                    document=document,
                    record_data=record,
                    validation_status=record["validation_status"],
                    errors=record["errors"],
                )
                for record in validated_records
            ]

            DocumentResult.objects.bulk_create(results)

            document.status = Document.Status.COMPLETED
            document.error_message = ""
            document.save(update_fields=["status", "error_message", "updated_at"])

    except (ValueError, FileNotFoundError) as error:
        if document is not None:
            document.status = Document.Status.FAILED
            document.error_message = str(error)[:2000]
            document.save(update_fields=["status", "error_message", "updated_at"])

            if document.file:
                document.file.delete(save=False)
                document.file.name = ""
                document.save(update_fields=["file"])

        return Response(
            {
                "message": "The document could not be processed.",
                "error_code": "DOCUMENT_PROCESSING_FAILED",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        logger.exception("Unexpected document processing failure")

        if document is not None:
            document.status = Document.Status.FAILED
            document.error_message = "An unexpected processing error occurred."
            document.save(update_fields=["status", "error_message", "updated_at"])

            if document.file:
                document.file.delete(save=False)
                document.file.name = ""
                document.save(update_fields=["file"])

        return Response(
            {
                "message": "An unexpected error occurred while processing the document.",
                "error_code": "INTERNAL_PROCESSING_ERROR",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    total_records = len(validated_records)
    valid_records = sum(
        record["validation_status"] == "valid"
        for record in validated_records
    )

    return Response(
        {
            "message": "Document processed successfully.",
            "data": {
                "id": document.id,
                "filename": document.original_filename,
                "status": document.status,
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": total_records - valid_records,
                "created_at": document.created_at.isoformat(),
            },
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["GET"])
def list_documents(request):
    documents = Document.objects.all()

    data = [
        {
            "id": document.id,
            "filename": document.original_filename,
            "status": document.status,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }
        for document in documents
    ]

    return Response(
        {
            "message": "Document history retrieved successfully.",
            "data": data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_document_result(request, document_id):
    document = get_object_or_404(Document, pk=document_id)

    results = document.results.all()

    return Response(
        {
            "message": "Document results retrieved successfully.",
            "data": {
                "document_id": document.id,
                "filename": document.original_filename,
                "status": document.status,
                "total_records": results.count(),
                "results": [
                    {
                        "record": result.record_data,
                        "validation_status": result.validation_status,
                        "errors": result.errors,
                    }
                    for result in results
                ],
            },
        },
        status=status.HTTP_200_OK,
    )
@api_view(["GET"])
def download_document_report(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    results = document.results.all()

    total_records = results.count()
    valid_records = results.filter(
        validation_status=DocumentResult.ValidationStatus.VALID
    ).count()
    invalid_records = total_records - valid_records

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    cell_style = ParagraphStyle(
        "ReportCell",
        parent=body_style,
        fontSize=7,
        leading=9,
        spaceAfter=0,
    )

    header_style = ParagraphStyle(
        "ReportHeader",
        parent=cell_style,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    document_pdf = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Document Processing Report {document.id}",
    )

    story = [
        Paragraph("Document Processing Report", title_style),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Document ID:</b> {document.id}", body_style),
        Paragraph(
            f"<b>Original filename:</b> {escape(document.original_filename)}",
            body_style,
        ),
        Paragraph(
            f"<b>Processing status:</b> {escape(document.status)}",
            body_style,
        ),
        Paragraph(
            f"<b>Report generated:</b> "
            f"{timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            body_style,
        ),
        Spacer(1, 3 * mm),
        Paragraph("Validation Summary", heading_style),
        Paragraph(f"<b>Total records:</b> {total_records}", body_style),
        Paragraph(f"<b>Valid records:</b> {valid_records}", body_style),
        Paragraph(f"<b>Invalid records:</b> {invalid_records}", body_style),
        Spacer(1, 5 * mm),
        Paragraph("Record Details", heading_style),
        Spacer(1, 2 * mm),
    ]

    headers = [
        "Invoice Number",
        "Vendor",
        "Invoice Date",
        "Total Amount",
        "Status",
        "Validation Errors",
    ]

    table_data = [
        [Paragraph(escape(header), header_style) for header in headers]
    ]

    for result in results.iterator():
        record = result.record_data or {}
        errors = result.errors or []

        if isinstance(errors, list):
            error_text = "; ".join(str(error) for error in errors)
        else:
            error_text = str(errors)

        values = [
            record.get("invoice_number", ""),
            record.get("vendor_name", ""),
            record.get("invoice_date", ""),
            record.get("total_amount", ""),
            result.validation_status,
            error_text,
        ]

        table_data.append([
            Paragraph(escape(str(value)), cell_style)
            for value in values
        ])

    if total_records == 0:
        table_data.append([
            Paragraph("No validation records found.", cell_style),
            "", "", "", "", "",
        ])

    report_table = LongTable(
        table_data,
        colWidths=[
            35 * mm,
            42 * mm,
            27 * mm,
            27 * mm,
            23 * mm,
            115 * mm,
        ],
        repeatRows=1,
        hAlign="LEFT",
    )

    report_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0057FF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.whitesmoke,
        ]),
    ]))

    story.append(report_table)
    document_pdf.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"document-{document.id}-report.pdf",
        content_type="application/pdf",
    )

@api_view(["GET", "DELETE"])
def document_detail(request, document_id):
    document = get_object_or_404(Document, pk=document_id)

    if request.method == "GET":
        return Response(
            {
                "message": "Document retrieved successfully.",
                "data": {
                    "id": document.id,
                    "filename": document.original_filename,
                    "status": document.status,
                    "error_message": document.error_message,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat(),
                    "total_records": document.results.count(),
                    "valid_records": document.results.filter(
                        validation_status=DocumentResult.ValidationStatus.VALID
                    ).count(),
                    "invalid_records": document.results.filter(
                        validation_status=DocumentResult.ValidationStatus.INVALID
                    ).count(),
                },
            },
            status=status.HTTP_200_OK,
        )

    file_name = document.file.name
    file_storage = document.file.storage

    try:
        with transaction.atomic():
            if file_name:
                file_storage.delete(file_name)
            document.delete()
    except Exception:
        logger.exception("Failed to delete document ID %s", document_id)
        return Response(
            {
                "message": "The document could not be deleted.",
                "error_code": "DOCUMENT_DELETE_FAILED",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "message": "Document and associated results deleted successfully.",
            "data": {"id": document_id, "deleted": True},
        },
        status=status.HTTP_200_OK,
    )
