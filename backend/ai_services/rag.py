"""
RAG orchestration. Framework-agnostic: takes plain values and a `RAGConfig`,
returns plain dicts. The Django layer builds the config from settings.
"""
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from . import AIServiceError, vector_store
from .chunking import chunk_pages
from .document_processing import extract_text
from .embeddings import embed_query, embed_texts
from .llm import get_llm, message_text


@dataclass
class RAGConfig:
    chroma_dir: str
    embedding_model: str
    llm_provider: str
    gemini_key: str = ""
    gemini_model: str = ""
    openai_key: str = ""
    openai_model: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5

    def llm(self, temperature: float = 0.2):
        return get_llm(
            self.llm_provider,
            gemini_key=self.gemini_key,
            gemini_model=self.gemini_model,
            openai_key=self.openai_key,
            openai_model=self.openai_model,
            temperature=temperature,
        )


QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a precise assistant that answers questions about ONE uploaded "
            "document. Use ONLY the context excerpts below. If the answer is not in "
            "the context, say you could not find it in the document - do not guess. "
            "Be concise and cite page numbers like (p. 3) when they are available.\n\n"
            "Context excerpts:\n{context}",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Summarize the following document for a busy reader. Give a 2-3 sentence "
            "overview followed by 5-8 bullet points of the key facts. Use only the text provided.",
        ),
        ("human", "{text}"),
    ]
)


def ingest_document(cfg: RAGConfig, *, user_id, document_id, path: str, file_type: str) -> dict:
    """Extract -> chunk -> embed -> store. Returns stats."""
    pages = extract_text(path, file_type)
    chunks = chunk_pages(pages, cfg.chunk_size, cfg.chunk_overlap)
    if not chunks:
        raise AIServiceError("Document produced no text chunks.")
    vectors = embed_texts([c.text for c in chunks], cfg.embedding_model)
    vector_store.add_chunks(cfg.chroma_dir, str(user_id), str(document_id), chunks, vectors)
    page_numbers = [p.page for p in pages if p.page is not None]
    return {"chunk_count": len(chunks), "page_count": max(page_numbers) if page_numbers else 0}


def answer_question(
    cfg: RAGConfig, *, user_id, document_id, question: str, history: list[dict] | None = None
) -> dict:
    """history: [{"role": "user"|"assistant", "content": str}, ...] oldest first."""
    hits = vector_store.query(
        cfg.chroma_dir,
        str(user_id),
        str(document_id),
        embed_query(question, cfg.embedding_model),
        cfg.top_k,
    )
    if not hits:
        return {"answer": "I could not find anything relevant in this document.", "sources": []}

    context = "\n\n".join(
        f"[Excerpt {i}{', p. ' + str(h['page']) if h['page'] else ''}]\n{h['text']}"
        for i, h in enumerate(hits, start=1)
    )
    messages = [
        (HumanMessage if m["role"] == "user" else AIMessage)(content=m["content"])
        for m in (history or [])
    ]
    chain = QA_PROMPT | cfg.llm()
    try:
        response = chain.invoke({"context": context, "history": messages, "question": question})
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"The language model request failed: {exc}") from exc

    sources = [
        {
            "page": h["page"],
            "score": h["score"],
            "snippet": h["text"][:300] + ("..." if len(h["text"]) > 300 else ""),
        }
        for h in hits
    ]
    return {"answer": message_text(response), "sources": sources}


def summarize_document(cfg: RAGConfig, *, path: str, file_type: str, max_chars: int = 12000) -> str:
    pages = extract_text(path, file_type)
    text = "\n\n".join(p.text for p in pages)
    if len(text) > max_chars:  # head + middle + tail keeps overall coverage
        third = max_chars // 3
        mid = len(text) // 2
        text = (
            text[:third]
            + "\n...\n"
            + text[mid - third // 2 : mid + third // 2]
            + "\n...\n"
            + text[-third:]
        )
    try:
        response = (SUMMARY_PROMPT | cfg.llm(temperature=0.3)).invoke({"text": text})
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"The language model request failed: {exc}") from exc
    return message_text(response)
