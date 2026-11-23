"""
ChromaDB vector store with strict per-user / per-document isolation.

Every vector is stored with `user_id` and `document_id` metadata, and every
query/delete is filtered on BOTH, so one user can never retrieve another
user's chunks even if a document id leaks.
"""
import threading

import chromadb

from .chunking import Chunk

COLLECTION_NAME = "documents"
_clients: dict[str, chromadb.api.ClientAPI] = {}
_lock = threading.Lock()


def _collection(persist_dir: str):
    with _lock:
        client = _clients.get(persist_dir)
        if client is None:
            client = chromadb.PersistentClient(path=persist_dir)
            _clients[persist_dir] = client
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def _where(user_id: str, document_id: str) -> dict:
    return {"$and": [{"user_id": str(user_id)}, {"document_id": str(document_id)}]}


def add_chunks(
    persist_dir: str,
    user_id: str,
    document_id: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> int:
    if not chunks:
        return 0
    col = _collection(persist_dir)
    # Make re-processing idempotent.
    col.delete(where=_where(user_id, document_id))
    col.add(
        ids=[f"{document_id}:{c.index}" for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "chunk_index": c.index,
                "page": c.page if c.page is not None else -1,
            }
            for c in chunks
        ],
    )
    return len(chunks)


def query(
    persist_dir: str, user_id: str, document_id: str, embedding: list[float], top_k: int = 5
) -> list[dict]:
    col = _collection(persist_dir)
    res = col.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=_where(user_id, document_id),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "page": None if meta.get("page", -1) == -1 else meta["page"],
                "chunk_index": meta.get("chunk_index"),
                "score": round(1 - dist, 4),  # cosine similarity
            }
        )
    return hits


def delete_document(persist_dir: str, user_id: str, document_id: str) -> None:
    _collection(persist_dir).delete(where=_where(user_id, document_id))
