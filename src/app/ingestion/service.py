import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from src.app.chunking.splitter import split_text
from src.app.config import Settings
from src.app.ingestion.parsers import DocumentParseError, parse_document
from src.app.schemas.documents import DocumentUploadResponse

logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES = {"txt", "md", "pdf"}


class DocumentIngestionError(ValueError):
    pass


async def ingest_document(file: UploadFile, settings: Settings) -> DocumentUploadResponse:
    source_name = file.filename or "uploaded_file"
    file_type = _extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        allowed_types = ", ".join(f".{item}" for item in sorted(ALLOWED_FILE_TYPES))
        raise DocumentIngestionError(
            f"Unsupported file type: .{file_type or 'unknown'}. Allowed types: {allowed_types}"
        )

    document_id = f"doc_{uuid4().hex}"
    upload_dir = Path(settings.data_dir) / settings.upload_dir_name
    chunk_dir = Path(settings.data_dir) / settings.chunk_dir_name
    upload_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    stored_path = upload_dir / f"{document_id}.{file_type}"
    chunk_path = chunk_dir / f"{document_id}.json"

    logger.info("Start ingesting document: source_name=%s document_id=%s", source_name, document_id)
    await _save_upload_file(file, stored_path)
    logger.info("Uploaded file saved: path=%s", stored_path)

    try:
        text = parse_document(stored_path, file_type)
    except DocumentParseError as error:
        logger.warning("Document parse failed: document_id=%s error=%s", document_id, error)
        raise DocumentIngestionError(str(error)) from error

    logger.info("Document parsed: document_id=%s characters=%s", document_id, len(text))
    chunks = split_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise DocumentIngestionError("Parsed document is empty")

    _write_chunks_file(
        chunk_path=chunk_path,
        document_id=document_id,
        source_name=source_name,
        file_type=file_type,
        chunks=chunks,
    )
    logger.info("Document chunks saved: document_id=%s chunk_count=%s", document_id, len(chunks))

    return DocumentUploadResponse(
        document_id=document_id,
        source_name=source_name,
        file_type=file_type,
        status="active",
        stored_path=str(stored_path),
        chunk_path=str(chunk_path),
        chunk_count=len(chunks),
        error_message=None,
    )


def _extract_file_type(filename: str) -> str:
    return Path(filename).suffix.removeprefix(".").lower()


async def _save_upload_file(file: UploadFile, stored_path: Path) -> None:
    contents = await file.read()
    if not contents:
        raise DocumentIngestionError("Uploaded file is empty")
    stored_path.write_bytes(contents)


def _write_chunks_file(
    chunk_path: Path,
    document_id: str,
    source_name: str,
    file_type: str,
    chunks: list,
) -> None:
    # 这一步先落 JSON 而不是进数据库，是为了先观察 chunking 效果，避免过早引入数据层。
    payload = {
        "document_id": document_id,
        "source_name": source_name,
        "file_type": file_type,
        "chunk_count": len(chunks),
        "chunks": [chunk.model_dump() for chunk in chunks],
    }
    chunk_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
