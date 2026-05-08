from sqlalchemy.orm import Session

from personal_growth_rag.domain.documents import TextChunk
from personal_growth_rag.infrastructure.db.models import Chunk
from personal_growth_rag.utils.hashing import hash_text
from personal_growth_rag.utils.ids import new_chunk_id


def add_chunks(db: Session, document_id: str, chunks: list[TextChunk]) -> list[Chunk]:
    chunk_rows = [
        Chunk(
            id=new_chunk_id(),
            document_id=document_id,
            chunk_order=chunk.chunk_order,
            text=chunk.text,
            content_hash=hash_text(chunk.text),
        )
        for chunk in chunks
    ]
    db.add_all(chunk_rows)
    return chunk_rows
