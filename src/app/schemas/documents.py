from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    source_name: str
    file_type: str
    status: str
    stored_path: str
    chunk_path: str
    chunk_count: int
    error_message: str | None = None
