
import pytest

from document_processing.processors import read_document


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_document("sample_data/missing_file.csv")


def test_unsupported_file_type(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("sample data")

    with pytest.raises(ValueError, match="Unsupported file type"):
        read_document(file_path)


def test_empty_csv(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("")

    with pytest.raises(ValueError, match="CSV file is empty"):
        read_document(file_path)


def test_empty_excel_file(tmp_path):
    file_path = tmp_path / "empty.xlsx"

    import pandas as pd
    pd.DataFrame().to_excel(file_path, index=False)

    with pytest.raises(ValueError, match="no data rows"):
        read_document(file_path)


def test_valid_csv(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text(
        "invoice_number,vendor_name\nINV-1001,ABC Technologies"
    )

    records = read_document(file_path)

    assert len(records) == 1
    assert records[0]["invoice_number"] == "INV-1001"
    assert records[0]["vendor_name"] == "ABC Technologies"


def test_rejects_file_over_size_limit(tmp_path, monkeypatch):
    import document_processing.processors as processors

    file_path = tmp_path / "large.csv"
    file_path.write_text("invoice_number\nINV-101\n")

    monkeypatch.setattr(processors, "MAX_FILE_SIZE_BYTES", 5)

    with pytest.raises(ValueError, match="maximum allowed size"):
        read_document(file_path)
