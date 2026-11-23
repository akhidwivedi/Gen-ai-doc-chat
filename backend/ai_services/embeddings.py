"""Sentence Transformers embeddings (lazy-loaded singleton)."""
import threading

from . import AIServiceError

_model = None
_model_name = None
_lock = threading.Lock()


def get_model(model_name: str):
    global _model, _model_name
    with _lock:
        if _model is None or _model_name != model_name:
            try:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(model_name)
                _model_name = model_name
            except Exception as exc:
                raise AIServiceError(f"Could not load embedding model '{model_name}': {exc}") from exc
    return _model


def embed_texts(texts: list[str], model_name: str, batch_size: int = 32) -> list[list[float]]:
    model = get_model(model_name)
    vectors = model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
    )
    return vectors.tolist()


def embed_query(text: str, model_name: str) -> list[float]:
    return embed_texts([text], model_name)[0]
