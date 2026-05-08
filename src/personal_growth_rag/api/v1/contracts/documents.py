"""Documents API request/response contracts。"""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    source_name: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]


class DocumentUploadResponse(BaseModel):
    document_id: str
    source_name: str
    file_type: str
    status: str
    chunk_count: int
