import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.app.config import Settings, get_settings
from src.app.ingestion.service import DocumentIngestionError, ingest_document
from src.app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
)
from src.app.storage.database import get_db_session
from src.app.storage.models import Document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentUploadResponse:
    try:
        return await ingest_document(file, settings, db)
    except DocumentIngestionError as error:
        logger.warning("Document upload rejected: filename=%s error=%s", file.filename, error)
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Annotated[Session, Depends(get_db_session)]) -> DocumentListResponse:
    documents = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return DocumentListResponse(items=[_to_document_summary(document) for document in documents])


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> DocumentDetailResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_document_detail(document)


def _to_document_summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        document_id=document.id,
        source_name=document.source_name,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _to_document_detail(document: Document) -> DocumentDetailResponse:
    return DocumentDetailResponse(
        **_to_document_summary(document).model_dump(),
        stored_path=document.stored_path,
        chunk_path=document.chunk_path,
        error_message=document.error_message,
    )
