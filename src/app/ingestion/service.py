import hashlib
import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.app.chunking.splitter import TextChunk, split_text
from src.app.config import Settings
from src.app.ingestion.parsers import DocumentParseError, parse_document
from src.app.schemas.documents import DocumentUploadResponse
from src.app.storage.models import Chunk, Document

logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES = {"txt", "md", "pdf"}


class DocumentIngestionError(ValueError):
    pass


async def ingest_document(
    file: UploadFile,
    settings: Settings,
    db: Session,
) -> DocumentUploadResponse:
    source_name = file.filename or "uploaded_file"
    file_type = _extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        allowed_types = ", ".join(f".{item}" for item in sorted(ALLOWED_FILE_TYPES))
        raise DocumentIngestionError(
            f"Unsupported file type: .{file_type or 'unknown'}. Allowed types: {allowed_types}"
        )

    contents = await _read_upload_file(file)
    content_hash = _hash_bytes(contents)

    document_id = f"doc_{uuid4().hex}"
    upload_dir = Path(settings.data_dir) / settings.upload_dir_name
    chunk_dir = Path(settings.data_dir) / settings.chunk_dir_name
    upload_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    stored_path = upload_dir / f"{document_id}.{file_type}"
    chunk_path = chunk_dir / f"{document_id}.json"

    document = Document(
        id=document_id,
        source_name=source_name,
        file_type=file_type,
        status="processing",
        content_hash=content_hash,
        stored_path=str(stored_path),
        chunk_path=str(chunk_path),
        chunk_count=0,
        error_message=None,
    )
    db.add(document)
    db.commit()

    logger.info("Start ingesting document: source_name=%s document_id=%s", source_name, document_id)
    try:
        stored_path.write_bytes(contents)
        logger.info("Uploaded file saved: path=%s", stored_path)

        text = parse_document(stored_path, file_type)
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
        _write_chunks_to_db(db=db, document_id=document_id, chunks=chunks)

        document.status = "active"
        document.chunk_count = len(chunks)
        document.error_message = None
        db.commit()
        db.refresh(document)

        logger.info(
            "Document chunks saved: document_id=%s chunk_count=%s", document_id, len(chunks)
        )
    except DocumentParseError as error:
        logger.warning("Document parse failed: document_id=%s error=%s", document_id, error)
        _mark_document_failed(db, document.id, str(error))
        raise DocumentIngestionError(str(error)) from error
    except Exception as error:
        logger.warning("Document ingest failed: document_id=%s error=%s", document_id, error)
        _mark_document_failed(db, document.id, str(error))
        if isinstance(error, DocumentIngestionError):
            raise
        raise DocumentIngestionError(str(error)) from error

    return DocumentUploadResponse(
        document_id=document.id,
        source_name=document.source_name,
        file_type=document.file_type,
        status=document.status,
        stored_path=document.stored_path,
        chunk_path=document.chunk_path,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
    )


def _extract_file_type(filename: str) -> str:
    return Path(filename).suffix.removeprefix(".").lower()


async def _read_upload_file(file: UploadFile) -> bytes:
    contents = await file.read()
    if not contents:
        raise DocumentIngestionError("Uploaded file is empty")
    return contents


def _hash_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_chunks_file(
    chunk_path: Path,
    document_id: str,
    source_name: str,
    file_type: str,
    chunks: list[TextChunk],
) -> None:
    # JSON 文件保留为调试产物，便于肉眼观察 chunking 效果；数据库是后续 RAG 主存储。
    payload = {
        "document_id": document_id,
        "source_name": source_name,
        "file_type": file_type,
        "chunk_count": len(chunks),
        "chunks": [chunk.model_dump() for chunk in chunks],
    }
    chunk_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_chunks_to_db(db: Session, document_id: str, chunks: list[TextChunk]) -> None:
    db.add_all(
        Chunk(
            id=f"chk_{uuid4().hex}",
            document_id=document_id,
            chunk_order=chunk.chunk_order,
            text=chunk.text,
            content_hash=_hash_text(chunk.text),
        )
        for chunk in chunks
    )


def _mark_document_failed(db: Session, document_id: str, error_message: str) -> None:
    db.rollback()
    document = db.get(Document, document_id)
    if document is None:
        return
    document.status = "failed"
    document.error_message = error_message
    db.commit()
