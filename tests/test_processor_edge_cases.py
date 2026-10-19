
import json

import pandas as pd
import pytest

from document_processing.processors import read_document


def test_preserves_leading_zero_invoice_number(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_text(
        "invoice_number,vendor_name,invoice_date,total_amount\n"
        "00123,ABC Technologies,2026-10-15,1200\n",
        encoding="utf-8",
    )

    records = read_document(file_path)

    assert records[0]["invoice_number"] == "00123"


def test_blank_excel_date_stays_blank(tmp_path):
    file_path = tmp_path / "invoices.xlsx"

    pd.DataFrame([{
        "invoice_number": "INV-1",
        "vendor_name": "ABC Technologies",
        "invoice_date": None,
        "total_amount": "1200",
    }]).to_excel(file_path, index=False)

    records = read_document(file_path)

    assert records[0]["invoice_date"] == ""


def test_excel_records_are_json_serializable(tmp_path):
    file_path = tmp_path / "invoices.xlsx"

    pd.DataFrame([{
        "invoice_number": "INV-2",
        "vendor_name": "ABC Technologies",
        "invoice_date": pd.Timestamp("2026-10-15"),
        "total_amount": 1200,
    }]).to_excel(file_path, index=False)

    records = read_document(file_path)

    json.dumps(records)


def test_detects_semicolon_csv(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_text(
        "invoice_number;vendor_name;invoice_date;total_amount\n"
        "00123;ABC Technologies;2026-10-15;1200\n",
        encoding="utf-8",
    )

    records = read_document(file_path)

    assert records[0]["invoice_number"] == "00123"
    assert records[0]["vendor_name"] == "ABC Technologies"


def test_reads_windows_1252_csv(tmp_path):
    file_path = tmp_path / "invoices.csv"
    file_path.write_bytes(
        "invoice_number,vendor_name,invoice_date,total_amount\n"
        "INV-3,Café Services,2026-10-15,1200\n".encode("cp1252")
    )

    records = read_document(file_path)

    assert records[0]["vendor_name"] == "Café Services"
