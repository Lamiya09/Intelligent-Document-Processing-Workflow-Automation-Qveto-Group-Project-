
import math
from datetime import date, datetime

import pandas as pd


REQUIRED_FIELDS = [
    "invoice_number",
    "vendor_name",
    "invoice_date",
    "total_amount",
]


def _is_blank(value):
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False


def _validate_amount(value, errors):
    if _is_blank(value):
        return

    # Boolean values must not be accepted as amounts.
    if isinstance(value, bool):
        errors.append("Invalid total_amount")
        return

    try:
        cleaned_value = str(value).strip()
        cleaned_value = cleaned_value.replace(",", "")

        if cleaned_value.startswith("$"):
            cleaned_value = cleaned_value[1:].strip()

        amount = float(cleaned_value)

        if not math.isfinite(amount):
            errors.append("Invalid total_amount")
        elif amount < 0:
            errors.append("Negative total_amount")
        else:
            return amount

    except (ValueError, TypeError):
        errors.append("Invalid total_amount")

    return None


def _validate_date(value):
    if _is_blank(value):
        return False

    if isinstance(value, (date, datetime, pd.Timestamp)):
        return True

    text = str(value).strip()

    # ISO dates are preferred because their meaning is unambiguous.
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        pass

    # For slash-separated dates, reject ambiguous day/month order.
    parts = text.split("/")

    if len(parts) == 3 and all(part.isdigit() for part in parts):
        first = int(parts[0])
        second = int(parts[1])

        if first <= 12 and second <= 12:
            return False

        for date_format in ("%d/%m/%Y", "%m/%d/%Y"):
            try:
                datetime.strptime(text, date_format)
                return True
            except ValueError:
                continue

    return False


def validate_records(records):
    if not isinstance(records, list):
        raise ValueError("records must be a list of dictionaries")

    results = []
    seen_invoice_numbers = set()

    for original in records:
        if not isinstance(original, dict):
            results.append({
                "errors": ["Invalid record: expected a dictionary"],
                "validation_status": "invalid",
            })
            continue

        row = dict(original)
        errors = []

        for field in REQUIRED_FIELDS:
            if _is_blank(row.get(field)):
                errors.append(f"Missing {field}")

        invoice_number = str(
            row.get("invoice_number", "")
        ).strip()

        if invoice_number:
            duplicate_key = invoice_number.casefold()

            if duplicate_key in seen_invoice_numbers:
                errors.append("Duplicate invoice_number")

            seen_invoice_numbers.add(duplicate_key)

        amount = _validate_amount(
            row.get("total_amount"), errors
        )

        if amount is not None:
            row["total_amount"] = amount

        date_value = row.get("invoice_date")

        if not _is_blank(date_value):
            if not _validate_date(date_value):
                errors.append("Invalid invoice_date")

        row["errors"] = errors
        row["validation_status"] = (
            "invalid" if errors else "valid"
        )

        results.append(row)

    return results
