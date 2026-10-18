
from pathlib import Path

import pandas as pd


def read_document(file_path):
    """Read a CSV or Excel document and return its records."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    extension = path.suffix.lower()

    if extension not in [".csv", ".xlsx"]:
        raise ValueError(f"Unsupported file type: {extension}")

    try:
        if extension == ".csv":
            data = pd.read_csv(path)
        else:
            data = pd.read_excel(path)

        if data.empty:
            raise ValueError("The document contains no data rows.")

        return data.fillna("").to_dict(orient="records")

    except pd.errors.EmptyDataError as error:
        raise ValueError("The CSV file is empty.") from error

    except (pd.errors.ParserError, ImportError, OSError) as error:
        raise ValueError(
            f"Could not read the document: {path.name}"
        ) from error
