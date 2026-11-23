"""
Reusable GenAI building blocks. Nothing in this package imports Django models,
so every module can be reused from scripts, notebooks or other projects.

    document_processing -> text extraction (PyMuPDF, python-docx)
    chunking            -> LangChain text splitting
    embeddings          -> Sentence Transformers
    vector_store        -> ChromaDB with per-user/per-document filtering
    llm                 -> Gemini / OpenAI via LangChain
    rag                 -> orchestration: ingest, answer, summarize
"""


class AIServiceError(Exception):
    """Raised for expected AI-pipeline failures that should be shown to the user."""
