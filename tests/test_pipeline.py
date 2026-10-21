
import pandas as pd
import pytest

from document_processing.pipeline import process_invoice_file


def test_process_invoice_csv_with_valid_and_invalid_rows(tmp_path):
    file_path = tmp_path / "invoices.csv"

    pd.DataFrame([
        {
            "invoice_number": "INV-1001",
            "vendor_name": "ABC Technologies",
            "invoice_date": "2026-10-15",
            "total_amount": "1500.00",
        },
        {
            "invoice_number": "INV-1002",
            "vendor_name": "",
            "invoice_date": "2026-10-16",
            "total_amount": "2000.00",
        },
    ]).to_csv(file_path, index=False)

    result = process_invoice_file(file_path)

    assert result["file_name"] == "invoices.csv"
    assert result["total_records"] == 2
    assert result["valid_records"] == 1
    assert result["invalid_records"] == 1
    assert result["results"][0]["validation_status"] == "valid"
    assert result["results"][1]["validation_status"] == "invalid"
    assert "Missing vendor_name" in result["results"][1]["errors"]


def test_process_invoice_excel_with_valid_row(tmp_path):
    file_path = tmp_path / "invoices.xlsx"

    pd.DataFrame([{
        "invoice_number": "INV-2001",
        "vendor_name": "XYZ Solutions",
        "invoice_date": "2026-10-15",
        "total_amount": "2500.00",
    }]).to_excel(file_path, index=False)

    result = process_invoice_file(file_path)

    assert result["total_records"] == 1
    assert result["valid_records"] == 1
    assert result["invalid_records"] == 0


def test_pipeline_rejects_pdf_for_invoice_validation(tmp_path):
    file_path = tmp_path / "invoice.pdf"
    file_path.write_bytes(b"not used by this test")

    with pytest.raises(ValueError, match="CSV and Excel"):
        process_invoice_file(file_path)
