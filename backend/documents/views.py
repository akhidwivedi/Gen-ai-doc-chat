from pathlib import Path

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ai_services import AIServiceError

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services import delete_document_everywhere, process_document, summarize


class DocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    list     GET    /api/documents/
    retrieve GET    /api/documents/{id}/
    create   POST   /api/documents/            (multipart: file, title?)
    destroy  DELETE /api/documents/{id}/
    summarize POST  /api/documents/{id}/summarize/
    reprocess POST  /api/documents/{id}/reprocess/

    Every query is scoped to request.user, so other users' documents are 404.
    """

    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "upload"
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        upload = DocumentUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        f = upload.validated_data["file"]
        ext = Path(f.name).suffix.lower().lstrip(".")
        title = upload.validated_data.get("title") or Path(f.name).stem
        doc = Document.objects.create(
            owner=request.user,
            title=title[:255],
            original_filename=Path(f.name).name[:255],
            file=f,
            file_type=ext,
            file_size=f.size,
        )
        doc = process_document(doc)
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        delete_document_everywhere(instance)

    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        doc = process_document(self.get_object())
        return Response(DocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def summarize(self, request, pk=None):
        doc = self.get_object()
        if doc.status != Document.Status.READY:
            return Response(
                {"detail": "Document is not ready yet."}, status=status.HTTP_409_CONFLICT
            )
        try:
            summarize(doc)
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        doc.refresh_from_db()
        return Response(DocumentSerializer(doc).data)
