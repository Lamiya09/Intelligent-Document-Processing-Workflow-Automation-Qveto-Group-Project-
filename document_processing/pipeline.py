
from pathlib import Path

from document_processing.processors import read_document
from document_processing.validators import validate_records


def process_invoice_file(file_path):
    """Read an invoice file and validate its extracted records."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in {".csv", ".xlsx"}:
        raise ValueError(
            "Invoice validation pipeline supports CSV and Excel files only."
        )

    records = read_document(path)
    results = validate_records(records)

    valid_count = sum(
        result["validation_status"] == "valid"
        for result in results
    )
    invalid_count = len(results) - valid_count

    return {
        "file_name": path.name,
        "total_records": len(results),
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "results": results,
    }
