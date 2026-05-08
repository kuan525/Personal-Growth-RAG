from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    source_name: str
    chunk_id: str
    chunk_order: int
    score: float
    text: str
