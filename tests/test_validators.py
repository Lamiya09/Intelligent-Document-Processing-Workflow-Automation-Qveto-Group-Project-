
from document_processing.validators import validate_records


def test_valid_invoice():
    records = [{
        "invoice_number": "INV-3001",
        "vendor_name": "ABC Technologies",
        "invoice_date": "2026-10-15",
        "total_amount": 1500.00,
    }]

    result = validate_records(records)

    assert result[0]["validation_status"] == "valid"
    assert result[0]["errors"] == []


def test_missing_vendor_name():
    records = [{
        "invoice_number": "INV-3002",
        "vendor_name": "",
        "invoice_date": "2026-10-15",
        "total_amount": 1500.00,
    }]

    result = validate_records(records)

    assert result[0]["validation_status"] == "invalid"
    assert "Missing vendor_name" in result[0]["errors"]


def test_negative_amount():
    records = [{
        "invoice_number": "INV-3003",
        "vendor_name": "Demo Services",
        "invoice_date": "2026-10-15",
        "total_amount": -500,
    }]

    result = validate_records(records)

    assert result[0]["validation_status"] == "invalid"
    assert "Negative total_amount" in result[0]["errors"]


def test_duplicate_invoice_number():
    records = [
        {
            "invoice_number": "INV-3004",
            "vendor_name": "ABC Technologies",
            "invoice_date": "2026-10-15",
            "total_amount": 1000,
        },
        {
            "invoice_number": "INV-3004",
            "vendor_name": "XYZ Solutions",
            "invoice_date": "2026-10-16",
            "total_amount": 2000,
        },
    ]

    result = validate_records(records)

    assert result[0]["validation_status"] == "valid"
    assert result[1]["validation_status"] == "invalid"
    assert "Duplicate invoice_number" in result[1]["errors"]
