
from pathlib import Path
import csv
import io

import pandas as pd
import pymupdf
import pytesseract
from PIL import Image


MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_PDF_PAGES = 100


# Update this path if Tesseract is installed elsewhere.
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def _read_pdf(path):
    """Extract text from digital PDFs and OCR scanned PDF pages."""
    extracted_pages = []

    try:
        with pymupdf.open(path) as pdf:
            if pdf.page_count == 0:
                raise ValueError("The PDF contains no pages.")

            if pdf.page_count > MAX_PDF_PAGES:
                raise ValueError(
                    "PDF exceeds the maximum allowed page count (100)."
                )

            for page in pdf:
                # First, extract selectable text from the PDF.
                text = page.get_text("text").strip()

                # If no text exists, try OCR for scanned pages.
                if not text:
                    pixmap = page.get_pixmap(dpi=200)
                    image_bytes = pixmap.tobytes("png")

                    with Image.open(io.BytesIO(image_bytes)) as image:
                        text = pytesseract.image_to_string(
                            image,
                            lang="eng",
                        ).strip()

                if text:
                    extracted_pages.append(text)

    except ValueError:
        raise
    except (
        pymupdf.FileDataError,
        RuntimeError,
        OSError,
        pytesseract.TesseractNotFoundError,
        pytesseract.TesseractError,
    ) as error:
        raise ValueError(
            f"Could not read the PDF file: {path.name}"
        ) from error

    if not extracted_pages:
        raise ValueError(
            "The PDF contains no extractable text. "
            "It may be empty or unreadable."
        )

    return [{"text": "\n".join(extracted_pages)}]


def read_document(file_path):
    """Read CSV, Excel, or PDF and return JSON-friendly records."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            "File exceeds the maximum allowed size of 50 MB."
        )

    extension = path.suffix.lower()

    if extension not in [".csv", ".xlsx", ".pdf"]:
        raise ValueError(f"Unsupported file type: {extension}")

    try:
        # PDF processing
        if extension == ".pdf":
            if path.stat().st_size == 0:
                raise ValueError("The PDF file is empty.")

            return _read_pdf(path)

        # CSV processing
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

        # Excel processing
        else:
            try:
                data = pd.read_excel(
                    path,
                    dtype=str,
                    keep_default_na=False,
                )
            except ValueError as error:
                raise ValueError(
                    f"Could not read the document: {path.name}"
                ) from error

        # Check whether the document contains any data.
        if data.empty or len(data.columns) == 0:
            raise ValueError("The document contains no data rows.")

        # Convert records into JSON-friendly dictionaries.
        return data.to_dict(orient="records")

    except ValueError:
        raise
    except (
        pd.errors.ParserError,
        OSError,
        ImportError,
    ) as error:
        raise ValueError(
            f"Could not read the document: {path.name}"
        ) from error
