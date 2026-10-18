
from pathlib import Path

import pandas as pd


def read_document(file_path):
    """Read a CSV or Excel document."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(path).fillna("").to_dict(orient="records")

    if extension == ".xlsx":
        return pd.read_excel(path).fillna("").to_dict(orient="records")

    raise ValueError(f"Unsupported file type: {extension}")
