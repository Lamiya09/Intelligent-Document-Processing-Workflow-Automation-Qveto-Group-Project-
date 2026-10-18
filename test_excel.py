
from pathlib import Path

import pandas as pd

from document_processing.processors import read_document

# Create a genuine Excel workbook for testing
excel_path = Path("sample_data/sample_invoices_test.xlsx")

sample_data = {
    "invoice_number": ["INV-2001", "INV-2002"],
    "vendor_name": ["ABC Technologies", "XYZ Solutions"],
    "invoice_date": ["2026-10-15", "2026-10-16"],
    "total_amount": [15000.00, 7250.50],
}

pd.DataFrame(sample_data).to_excel(excel_path, index=False)

# Read the workbook using our processing function
records = read_document(excel_path)

assert len(records) == 2
assert records[0]["invoice_number"] == "INV-2001"
assert records[1]["total_amount"] == 7250.50

print("PASS: Excel workbook read successfully.")
print("Records:", len(records))
print(records)
