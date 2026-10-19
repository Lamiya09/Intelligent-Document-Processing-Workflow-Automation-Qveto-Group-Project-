
from pathlib import Path
import csv

import pandas as pd


def read_document(file_path):
    """Read a CSV or Excel file and return JSON-friendly records."""

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
            if path.stat().st_size == 0:
                raise ValueError("The CSV file is empty.")

            try:
                data = pd.read_csv(
                    path,
                    dtype=str,
                    keep_default_na=False,
                    encoding="utf-8-sig",
                    sep=None,
                    engine="python",
                    on_bad_lines="error",
                )
            except UnicodeDecodeError:
                data = pd.read_csv(
                    path,
                    dtype=str,
                    keep_default_na=False,
                    encoding="cp1252",
                    sep=None,
                    engine="python",
                    on_bad_lines="error",
                )
            except csv.Error as error:
                raise ValueError(
                    "The CSV file is empty or has an invalid delimiter."
                ) from error

        else:
            data = pd.read_excel(
                path,
                dtype=str,
                keep_default_na=False,
            )

        if data.empty or len(data.columns) == 0:
            raise ValueError("The document contains no data rows.")

        return data.to_dict(orient="records")

    except pd.errors.EmptyDataError as error:
        raise ValueError("The CSV file is empty.") from error

    except (pd.errors.ParserError, OSError) as error:
        raise ValueError(
            f"Could not read the document: {path.name}"
        ) from error
