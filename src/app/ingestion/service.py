import hashlib
import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.app.chunking.splitter import TextChunk, split_text
from src.app.config import Settings
from src.app.embeddings.service import DashScopeEmbeddingService, iter_batches
from src.app.indexing.faiss_store import FaissIndexStore
from src.app.ingestion.parsers import DocumentParseError, parse_document
from src.app.schemas.documents import DocumentUploadResponse
from src.app.storage.models import Chunk, Document, Embedding

logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES = {"txt", "md", "pdf"}


class DocumentIngestionError(ValueError):
    pass


class DuplicateDocumentSkipped(RuntimeError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Duplicate active document skipped: {document_id}")
        self.document_id = document_id


async def ingest_document(
    file: UploadFile,
    settings: Settings,
    db: Session,
) -> DocumentUploadResponse:
    source_name = file.filename or "uploaded_file"
    file_type = _extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise DocumentIngestionError(_unsupported_file_type_message(file_type))

    contents = await _read_upload_file(file)
    return ingest_document_contents(
        source_name=source_name,
        file_type=file_type,
        contents=contents,
        settings=settings,
        db=db,
        skip_duplicate=False,
    )


def ingest_local_file(
    file_path: Path,
    settings: Settings,
    db: Session,
    *,
    skip_duplicate: bool = True,
) -> DocumentUploadResponse:
    source_name = file_path.name
    file_type = _extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise DocumentIngestionError(_unsupported_file_type_message(file_type))

    contents = file_path.read_bytes()
    if not contents:
        raise DocumentIngestionError("Uploaded file is empty")

    return ingest_document_contents(
        source_name=source_name,
        file_type=file_type,
        contents=contents,
        settings=settings,
        db=db,
        skip_duplicate=skip_duplicate,
    )


def ingest_document_contents(
    source_name: str,
    file_type: str,
    contents: bytes,
    settings: Settings,
    db: Session,
    *,
    skip_duplicate: bool,
) -> DocumentUploadResponse:
    content_hash = _hash_bytes(contents)
    if skip_duplicate:
        existing_document = _find_active_document_by_hash(db, content_hash)
        if existing_document is not None:
            raise DuplicateDocumentSkipped(existing_document.id)

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
        chunk_rows = _write_chunks_to_db(db=db, document_id=document_id, chunks=chunks)
        _write_embeddings_and_index(db=db, settings=settings, chunks=chunk_rows)

        document.status = "active"
        document.chunk_count = len(chunks)
        document.error_message = None
        db.commit()
        db.refresh(document)

        logger.info(
            "Document chunks indexed: document_id=%s chunk_count=%s", document_id, len(chunks)
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


def _unsupported_file_type_message(file_type: str) -> str:
    allowed_types = ", ".join(f".{item}" for item in sorted(ALLOWED_FILE_TYPES))
    return f"Unsupported file type: .{file_type or 'unknown'}. Allowed types: {allowed_types}"


def _find_active_document_by_hash(db: Session, content_hash: str) -> Document | None:
    return db.scalar(
        select(Document).where(Document.content_hash == content_hash, Document.status == "active")
    )


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


def _write_chunks_to_db(db: Session, document_id: str, chunks: list[TextChunk]) -> list[Chunk]:
    chunk_rows = [
        Chunk(
            id=f"chk_{uuid4().hex}",
            document_id=document_id,
            chunk_order=chunk.chunk_order,
            text=chunk.text,
            content_hash=_hash_text(chunk.text),
        )
        for chunk in chunks
    ]
    db.add_all(chunk_rows)
    return chunk_rows


def _write_embeddings_and_index(db: Session, settings: Settings, chunks: list[Chunk]) -> None:
    embedding_service = DashScopeEmbeddingService(settings)
    faiss_store = FaissIndexStore(settings)

    texts = [chunk.text for chunk in chunks]
    vectors: list[list[float]] = []
    for batch in iter_batches(texts, settings.embedding_batch_size):
        vectors.extend(embedding_service.embed_texts(batch))

    positions = faiss_store.add_vectors(vectors)
    db.add_all(
        Embedding(
            chunk_id=chunk.id,
            model_name=settings.embedding_model,
            vector_dim=settings.embedding_dim,
            index_position=position,
        )
        for chunk, position in zip(chunks, positions, strict=True)
    )


def _mark_document_failed(db: Session, document_id: str, error_message: str) -> None:
    db.rollback()
    document = db.get(Document, document_id)
    if document is None:
        return
    document.status = "failed"
    document.error_message = error_message
    db.commit()
