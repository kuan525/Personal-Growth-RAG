from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TextChunk:
    chunk_order: int
    text: str


@dataclass(frozen=True)
class DocumentSummaryData:
    document_id: str
    source_name: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DocumentDetailData(DocumentSummaryData):
    stored_path: str
    chunk_path: str
    error_message: str | None = None


@dataclass(frozen=True)
class DocumentIngestionResult:
    document_id: str
    source_name: str
    file_type: str
    status: str
    stored_path: str
    chunk_path: str
    chunk_count: int
    error_message: str | None = None
