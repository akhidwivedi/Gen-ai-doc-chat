"""Split extracted text into overlapping chunks, keeping page metadata."""
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .document_processing import PageText


@dataclass
class Chunk:
    text: str
    index: int
    page: int | None


def chunk_pages(
    pages: list[PageText], chunk_size: int = 1000, chunk_overlap: int = 150
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    for page in pages:
        for piece in splitter.split_text(page.text):
            piece = piece.strip()
            if piece:
                chunks.append(Chunk(text=piece, index=len(chunks), page=page.page))
    return chunks
