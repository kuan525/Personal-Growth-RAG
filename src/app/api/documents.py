import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.app.config import Settings, get_settings
from src.app.ingestion.service import DocumentIngestionError, ingest_document
from src.app.schemas.documents import DocumentUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentUploadResponse:
    try:
        return await ingest_document(file, settings)
    except DocumentIngestionError as error:
        logger.warning("Document upload rejected: filename=%s error=%s", file.filename, error)
        raise HTTPException(status_code=400, detail=str(error)) from error
