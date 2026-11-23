from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import Document

PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"  # DOCX is a zip container


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "title", "original_filename", "file_type", "file_size", "status",
            "error_message", "page_count", "chunk_count", "summary",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_file(self, f):
        ext = Path(f.name).suffix.lower().lstrip(".")
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}."
            )
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if f.size > max_bytes:
            raise serializers.ValidationError(f"File too large (max {settings.MAX_UPLOAD_MB} MB).")
        if f.size == 0:
            raise serializers.ValidationError("File is empty.")

        # Verify real content, not just the extension.
        head = f.read(8)
        f.seek(0)
        if ext == "pdf" and not head.startswith(PDF_MAGIC):
            raise serializers.ValidationError("File content is not a valid PDF.")
        if ext == "docx" and not head.startswith(ZIP_MAGIC):
            raise serializers.ValidationError("File content is not a valid DOCX.")
        if ext == "txt":
            sample = f.read(4096)
            f.seek(0)
            if b"\x00" in sample:
                raise serializers.ValidationError("File content is not plain text.")
        return f
