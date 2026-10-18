
from document_processing.processors import read_document
from document_processing.validators import validate_records

file_path = "sample_data/sample_invoices.csv"

records = read_document(file_path)
validated_records = validate_records(records)

print("Total records:", len(validated_records))

for record in validated_records:
    print(record["invoice_number"], record["validation_status"])
    print("Errors:", record["errors"])
