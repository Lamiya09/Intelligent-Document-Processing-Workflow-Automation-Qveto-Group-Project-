from django.urls import path

from .views import (
    health_check,
    upload_document,
    list_documents,
    get_document_result,
    document_detail,
    download_document_report,
)

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("documents", upload_document, name="document-upload"),
    path("documents/", list_documents, name="document-list"),
    path(
        "documents/<int:document_id>",
        document_detail,
        name="document-detail",
    ),
    path(
        "documents/<int:document_id>/result",
        get_document_result,
        name="document-result",
    ),
    path(
        "documents/<int:document_id>/download",
        download_document_report,
        name="document-download",
    ),
]