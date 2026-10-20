
import pymupdf
import pytest

from document_processing.processors import read_document
from PIL import Image, ImageDraw, ImageFont

def create_test_pdf(file_path, text="Invoice Number: INV-101"):
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), text)
        pdf.save(file_path)


def test_extracts_text_from_pdf(tmp_path):
    pdf_path = tmp_path / "invoice.pdf"
    create_test_pdf(pdf_path, "Invoice Number: INV-101")

    records = read_document(pdf_path)

    assert len(records) == 1
    assert "INV-101" in records[0]["text"]


def test_rejects_pdf_without_extractable_text(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    create_test_pdf(pdf_path, "   ")

    with pytest.raises(ValueError, match="no extractable text"):
        read_document(pdf_path)


def test_rejects_corrupted_pdf(tmp_path):
    pdf_path = tmp_path / "corrupted.pdf"
    pdf_path.write_bytes(b"This is not a valid PDF")

    with pytest.raises(ValueError, match="Could not read the PDF"):
        read_document(pdf_path)
def test_extracts_text_from_scanned_pdf(tmp_path):
    image_path = tmp_path / "scanned_invoice.png"
    pdf_path = tmp_path / "scanned_invoice.pdf"

    image = Image.new("RGB", (1200, 400), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (50, 100),
        "Invoice Number: INV-2026-101",
        fill="black",
    )
    image.save(image_path)

    with pymupdf.open() as pdf:
        page = pdf.new_page(width=600, height=200)
        page.insert_image(page.rect, filename=str(image_path))
        pdf.save(pdf_path)

    records = read_document(pdf_path)

    assert len(records) == 1
    assert "INV-2026-101" in records[0]["text"]

def test_extracts_text_from_multiple_scanned_pdf_pages(tmp_path):
    first_image_path = tmp_path / "page1.png"
    second_image_path = tmp_path / "page2.png"
    pdf_path = tmp_path / "multi_page_scanned.pdf"

    # Create the first scanned page.
    first_image = Image.new("RGB", (1200, 400), "white")
    first_draw = ImageDraw.Draw(first_image)
    first_draw.text(
        (50, 100),
        "Invoice Number: INV-PAGE-101",
        fill="black",
    )
    first_image.save(first_image_path)

    # Create the second scanned page.
    second_image = Image.new("RGB", (1200, 400), "white")
    second_draw = ImageDraw.Draw(second_image)
    second_draw.text(
        (50, 100),
        "Invoice Total: 2500",
        fill="black",
    )
    second_image.save(second_image_path)

    # Combine both images into one PDF.
    with pymupdf.open() as pdf:
        first_page = pdf.new_page(width=600, height=200)
        first_page.insert_image(
            first_page.rect,
            filename=str(first_image_path),
        )

        second_page = pdf.new_page(width=600, height=200)
        second_page.insert_image(
            second_page.rect,
            filename=str(second_image_path),
        )

        pdf.save(pdf_path)

    # Extract text from both scanned pages.
    records = read_document(pdf_path)

    assert len(records) == 1

    extracted_text = records[0]["text"]

    assert "INV-PAGE-101" in extracted_text
    assert "Invoice Total" in extracted_text
    assert "2500" in extracted_text

    # Confirm that page order is preserved.
    assert extracted_text.index("INV-PAGE-101") < extracted_text.index(
        "Invoice Total"
    )


def test_rejects_pdf_over_page_limit(tmp_path, monkeypatch):
    import document_processing.processors as processors

    pdf_path = tmp_path / "too_many_pages.pdf"

    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.new_page()
        pdf.save(pdf_path)

    monkeypatch.setattr(processors, "MAX_PDF_PAGES", 1)

    with pytest.raises(ValueError, match="maximum allowed page count"):
        read_document(pdf_path)
