
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