
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class DocumentResult(models.Model):
    class ValidationStatus(models.TextChoices):
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="results",
    )
    record_data = models.JSONField()
    validation_status = models.CharField(
        max_length=10,
        choices=ValidationStatus.choices,
        db_index=True,
    )
    errors = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=["document", "validation_status"],
                name="doc_result_status_idx",
            ),
        ]

    def __str__(self):
        return f"Document {self.document_id}: {self.validation_status}"
