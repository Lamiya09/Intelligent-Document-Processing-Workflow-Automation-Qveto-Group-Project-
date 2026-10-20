
import pytest

from document_processing.validators import validate_records


def make_invoice(**changes):
    record = {
        "invoice_number": "INV-1001",
        "vendor_name": "ABC Technologies",
        "invoice_date": "2026-10-15",
        "total_amount": "1200",
    }
    record.update(changes)
    return record


@pytest.mark.parametrize(
    "amount",
    ["NaN", "inf", "-inf", "True", True, float("nan"), float("inf")],
)
def test_rejects_invalid_amounts(amount):
    result = validate_records([
        make_invoice(total_amount=amount)
    ])
    assert "Invalid total_amount" in result[0]["errors"]


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("$1,200.00", 1200.0),
        ("1,200", 1200.0),
        ("1200", 1200.0),
    ],
)
def test_accepts_formatted_amounts(amount, expected):
    result = validate_records([
        make_invoice(total_amount=amount)
    ])
    assert result[0]["total_amount"] == expected
    assert result[0]["validation_status"] == "valid"


def test_detects_duplicate_invoice_numbers_case_insensitively():
    result = validate_records([
        make_invoice(invoice_number="INV-1001"),
        make_invoice(invoice_number="inv-1001"),
    ])
    assert "Duplicate invoice_number" in result[1]["errors"]


@pytest.mark.parametrize("invoice_date", ["", "not-a-date", "01/02/2026"])
def test_rejects_blank_invalid_and_ambiguous_dates(invoice_date):
    result = validate_records([
        make_invoice(invoice_date=invoice_date)
    ])
    assert result[0]["validation_status"] == "invalid"


def test_rejects_none_as_records_input():
    with pytest.raises(ValueError):
        validate_records(None)


def test_invalid_row_does_not_discard_valid_row():
    result = validate_records([
        make_invoice(),
        make_invoice(total_amount="not-money"),
    ])
    assert result[0]["validation_status"] == "valid"
    assert result[1]["validation_status"] == "invalid"
