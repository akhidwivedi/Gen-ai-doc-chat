"""Glue between Django (models/settings) and the framework-agnostic ai_services package."""
import logging

from django.conf import settings

from ai_services import AIServiceError, vector_store
from ai_services.rag import RAGConfig, ingest_document, summarize_document

from .models import Document

logger = logging.getLogger(__name__)


def get_rag_config() -> RAGConfig:
    return RAGConfig(
        chroma_dir=settings.CHROMA_DIR,
        embedding_model=settings.EMBEDDING_MODEL,
        llm_provider=settings.LLM_PROVIDER,
        gemini_key=settings.GEMINI_API_KEY,
        gemini_model=settings.GEMINI_MODEL,
        openai_key=settings.OPENAI_API_KEY,
        openai_model=settings.OPENAI_MODEL,
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        top_k=settings.RAG_TOP_K,
    )


def process_document(doc: Document) -> Document:
    """Extract, chunk, embed and index a document. Updates status fields."""
    doc.status = Document.Status.PROCESSING
    doc.error_message = ""
    doc.save(update_fields=["status", "error_message", "updated_at"])
    try:
        stats = ingest_document(
            get_rag_config(),
            user_id=doc.owner_id,
            document_id=doc.id,
            path=doc.file.path,
            file_type=doc.file_type,
        )
        doc.page_count = stats["page_count"]
        doc.chunk_count = stats["chunk_count"]
        doc.status = Document.Status.READY
    except AIServiceError as exc:
        doc.status = Document.Status.FAILED
        doc.error_message = str(exc)
    except Exception as exc:  # never leave a doc stuck in "processing"
        logger.exception("Unexpected error processing document %s", doc.id)
        doc.status = Document.Status.FAILED
        doc.error_message = f"Unexpected processing error: {exc}"
    doc.save()
    return doc


def delete_document_everywhere(doc: Document) -> None:
    """Remove vectors, the file on disk, then the DB row (messages cascade)."""
    try:
        vector_store.delete_document(settings.CHROMA_DIR, str(doc.owner_id), str(doc.id))
    except Exception:
        logger.exception("Failed to delete vectors for %s", doc.id)
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()


def summarize(doc: Document) -> str:
    summary = summarize_document(get_rag_config(), path=doc.file.path, file_type=doc.file_type)
    doc.summary = summary
    doc.save(update_fields=["summary", "updated_at"])
    return summary
