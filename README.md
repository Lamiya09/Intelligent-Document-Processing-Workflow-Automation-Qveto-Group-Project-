# Qveto — Intelligent Document Processing & Workflow Automation

A Django REST Framework API for uploading CSV and Excel invoice files, validating invoice records, storing processing results, retrieving document history, and downloading PDF reports.

## Features

- CSV and XLSX invoice uploads
- Invoice field validation
- Document processing status and history
- Structured JSON responses
- PDF processing reports
- Document deletion
- Automated tests

## Requirements

- Python 3.13+
- pip
- Git

## Local Setup

### 1. Clone the repository

```bash
git clone -b evaan-backend https://github.com/Lamiya09/Intelligent-Document-Processing-Workflow-Automation-Qveto-Group-Project-.git
cd Intelligent-Document-Processing-Workflow-Automation-Qveto-Group-Project-
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Set a private Django secret key and configure local development settings. See the project settings for the supported environment variables.

### 5. Apply database migrations

```powershell
python manage.py migrate
```

### 6. Start the development server

```powershell
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | Health check |
| POST | `/api/documents` | Upload and process a document |
| GET | `/api/documents/` | List documents |
| GET | `/api/documents/<id>` | Retrieve document details |
| GET | `/api/documents/<id>/result` | Retrieve processing results |
| GET | `/api/documents/<id>/download` | Download a PDF report |
| DELETE | `/api/documents/<id>` | Delete a document |

For uploads, send a multipart form request using the field name `file`. CSV and XLSX files are supported, with a maximum upload size of 10 MB.

Invoice fields validated by the current implementation:

- `invoice_number`
- `vendor_name`
- `invoice_date`
- `total_amount`

## Run Tests

```powershell
python -m pytest -q
```

## Security Notes

- Never commit `.env` files or secret keys.
- Configure a strong `DJANGO_SECRET_KEY` for deployment.
- Configure `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS` appropriately.
- Add authentication and document-ownership checks before exposing the API to multiple users or the public internet.
- Use a production-ready database and deployment configuration before production release.

## Project Status

This project is under development. Consult the implementation and tests for the currently supported behavior.
