from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from personal_growth_rag.api.v1.contracts.common import ApiResponse, ok
from personal_growth_rag.api.v1.contracts.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from personal_growth_rag.api.v1.deps import Settings, get_db_session, get_settings
from personal_growth_rag.application.documents.get_document import get_document
from personal_growth_rag.application.documents.ingest_document import ingest_uploaded_document
from personal_growth_rag.application.documents.list_documents import list_documents
from personal_growth_rag.domain.documents import DocumentDetailData, DocumentIngestionResult

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=ApiResponse[DocumentUploadResponse])
async def upload_document(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> ApiResponse[DocumentUploadResponse]:
    contents = await file.read()
    result = ingest_uploaded_document(file.filename or "uploaded_file", contents, settings, db)
    return ok(_to_upload_response(result))


@router.get("", response_model=ApiResponse[DocumentListResponse])
def list_document_route(
    db: Annotated[Session, Depends(get_db_session)]
) -> ApiResponse[DocumentListResponse]:
    items = [DocumentResponse(**document.__dict__) for document in list_documents(db)]
    return ok(DocumentListResponse(items=items))


@router.get("/{document_id}", response_model=ApiResponse[DocumentResponse])
def get_document_route(
    document_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    result = get_document(document_id, db)
    return ok(_to_document_response(result))


def _to_upload_response(result: DocumentIngestionResult) -> DocumentUploadResponse:
    return DocumentUploadResponse(
        document_id=result.document_id,
        source_name=result.source_name,
        file_type=result.file_type,
        status=result.status,
        chunk_count=result.chunk_count,
    )


def _to_document_response(result: DocumentDetailData) -> DocumentResponse:
    # stored_path/chunk_path/error_message 是内部排障字段，不暴露给成功态前端响应。
    return DocumentResponse(
        document_id=result.document_id,
        source_name=result.source_name,
        file_type=result.file_type,
        status=result.status,
        chunk_count=result.chunk_count,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
