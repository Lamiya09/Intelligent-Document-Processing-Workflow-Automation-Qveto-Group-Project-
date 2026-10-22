
import pandas as pd
import pytest

import json
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


def test_pipeline_rejects_missing_file(tmp_path):
    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        process_invoice_file(file_path)


def test_pipeline_rejects_unsupported_file_type(tmp_path):
    file_path = tmp_path / "invoices.txt"
    file_path.write_text("invoice data", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV and Excel"):
        process_invoice_file(file_path)


def test_pipeline_returns_zero_counts_for_header_only_csv(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_text(
        "invoice_number,vendor_name,invoice_date,total_amount\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no data rows"):
        process_invoice_file(file_path)


def test_pipeline_output_is_json_serializable(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_text(
        "invoice_number,vendor_name,invoice_date,total_amount\n"
        "INV-3001,ABC Technologies,2026-10-15,1500.00\n",
        encoding="utf-8",
    )

    result = process_invoice_file(file_path)

    # The full result should be convertible to JSON.
    json_output = json.dumps(result)
    restored_result = json.loads(json_output)

    assert restored_result["file_name"] == "invoices.csv"
    assert restored_result["total_records"] == 1
    assert restored_result["valid_records"] == 1
    assert restored_result["invalid_records"] == 0


def test_pipeline_counts_match_validation_results(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_text(
        "invoice_number,vendor_name,invoice_date,total_amount\n"
        "INV-4001,ABC Technologies,2026-10-15,1500.00\n"
        "INV-4002,,2026-10-16,2000.00\n"
        "INV-4003,XYZ Solutions,2026-10-17,3000.00\n",
        encoding="utf-8",
    )

    result = process_invoice_file(file_path)
    records = result["results"]

    actual_valid = sum(
        row["validation_status"] == "valid"
        for row in records
    )
    actual_invalid = sum(
        row["validation_status"] == "invalid"
        for row in records
    )

    assert result["total_records"] == len(records) == 3
    assert result["valid_records"] == actual_valid == 2
    assert result["invalid_records"] == actual_invalid == 1
