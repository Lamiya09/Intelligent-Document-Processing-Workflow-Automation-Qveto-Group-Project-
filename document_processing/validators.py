
import pandas as pd


REQUIRED_FIELDS = [
    "invoice_number",
    "vendor_name",
    "invoice_date",
    "total_amount",
]


def validate_records(records):
    results = []
    seen_invoice_numbers = set()

    for original in records:
        row = dict(original)
        errors = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            value = row.get(field)

            if value is None or str(value).strip() == "":
                errors.append(f"Missing {field}")

        # Check duplicate invoice numbers
        invoice_number = str(row.get("invoice_number", "")).strip()

        if invoice_number:
            if invoice_number in seen_invoice_numbers:
                errors.append("Duplicate invoice_number")

            seen_invoice_numbers.add(invoice_number)

        # Check amount
        amount = row.get("total_amount")

        try:
            if amount is None or str(amount).strip() == "":
                pass
            elif float(amount) < 0:
                errors.append("Negative total_amount")
            else:
                row["total_amount"] = float(amount)
        except (ValueError, TypeError):
            errors.append("Invalid total_amount")

        # Check date
        date_value = row.get("invoice_date")

        if date_value is not None and str(date_value).strip():
            try:
                pd.to_datetime(date_value, errors="raise")
            except (ValueError, TypeError):
                errors.append("Invalid invoice_date")

        row["errors"] = errors
        row["validation_status"] = "invalid" if errors else "valid"

        results.append(row)

    return results
