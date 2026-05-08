import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from personal_growth_rag.core.config import Settings
from personal_growth_rag.core.constants import (
    ALLOWED_FILE_TYPES,
    DOCUMENT_STATUS_PROCESSING,
)
from personal_growth_rag.core.errors import DocumentIngestionError, DuplicateDocumentSkipped
from personal_growth_rag.core.paths import chunk_dir, upload_dir
from personal_growth_rag.domain.documents import DocumentIngestionResult, TextChunk
from personal_growth_rag.infrastructure.chunking.recursive_splitter import split_text
from personal_growth_rag.infrastructure.db.models import Chunk, Document
from personal_growth_rag.infrastructure.db.repositories.chunks import add_chunks
from personal_growth_rag.infrastructure.db.repositories.documents import (
    add_document,
    find_active_document_by_hash,
    mark_document_active,
    mark_document_failed,
)
from personal_growth_rag.infrastructure.db.repositories.embeddings import add_embeddings
from personal_growth_rag.infrastructure.embeddings.batching import iter_batches
from personal_growth_rag.infrastructure.embeddings.dashscope import DashScopeEmbeddingClient
from personal_growth_rag.infrastructure.parsing.document_parser import (
    DocumentParseError,
    parse_document,
)
from personal_growth_rag.infrastructure.vectorstores.faiss_store import FaissVectorStore
from personal_growth_rag.utils.hashing import hash_bytes
from personal_growth_rag.utils.ids import new_document_id

logger = logging.getLogger(__name__)


def ingest_uploaded_document(
    source_name: str,
    contents: bytes,
    settings: Settings,
    db: Session,
) -> DocumentIngestionResult:
    file_type = extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise DocumentIngestionError(unsupported_file_type_message(file_type))
    if not contents:
        raise DocumentIngestionError("Uploaded file is empty")

    # HTTP 上传和 CLI 导入最终进入同一个 contents 级入口，保证链路一致。
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
) -> DocumentIngestionResult:
    source_name = file_path.name
    file_type = extract_file_type(source_name)
    if file_type not in ALLOWED_FILE_TYPES:
        raise DocumentIngestionError(unsupported_file_type_message(file_type))

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
) -> DocumentIngestionResult:
    content_hash = hash_bytes(contents)
    if skip_duplicate:
        existing_document = find_active_document_by_hash(db, content_hash)
        if existing_document is not None:
            raise DuplicateDocumentSkipped(existing_document.id)

    document_id = new_document_id()
    uploads = upload_dir(settings)
    chunks_dir = chunk_dir(settings)
    uploads.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    stored_path = uploads / f"{document_id}.{file_type}"
    chunk_path = chunks_dir / f"{document_id}.json"

    # 先落 processing 文档，再执行 parse/chunk/embed；失败时可保留错误状态。
    document = Document(
        id=document_id,
        source_name=source_name,
        file_type=file_type,
        status=DOCUMENT_STATUS_PROCESSING,
        content_hash=content_hash,
        stored_path=str(stored_path),
        chunk_path=str(chunk_path),
        chunk_count=0,
        error_message=None,
    )
    add_document(db, document)
    db.commit()

    logger.info("Start ingesting document: source_name=%s document_id=%s", source_name, document_id)
    try:
        stored_path.write_bytes(contents)
        text = parse_document(stored_path, file_type)
        chunks = split_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise DocumentIngestionError("Parsed document is empty")

        write_chunks_file(
            chunk_path=chunk_path,
            document_id=document_id,
            source_name=source_name,
            file_type=file_type,
            chunks=chunks,
        )
        chunk_rows = add_chunks(db=db, document_id=document_id, chunks=chunks)
        write_embeddings_and_index(db=db, settings=settings, chunks=chunk_rows)

        mark_document_active(db, document, len(chunks))
        db.commit()
        db.refresh(document)

        logger.info("Document indexed: document_id=%s chunk_count=%s", document_id, len(chunks))
    except DocumentParseError as error:
        logger.warning("Document parse failed: document_id=%s error=%s", document_id, error)
        mark_document_failed(db, document.id, str(error))
        raise DocumentIngestionError(str(error)) from error
    except Exception as error:
        logger.warning("Document ingest failed: document_id=%s error=%s", document_id, error)
        mark_document_failed(db, document.id, str(error))
        if isinstance(error, DocumentIngestionError):
            raise
        raise DocumentIngestionError(str(error)) from error

    return DocumentIngestionResult(
        document_id=document.id,
        source_name=document.source_name,
        file_type=document.file_type,
        status=document.status,
        stored_path=document.stored_path,
        chunk_path=document.chunk_path,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
    )


def extract_file_type(filename: str) -> str:
    return Path(filename).suffix.removeprefix(".").lower()


def unsupported_file_type_message(file_type: str) -> str:
    allowed_types = ", ".join(f".{item}" for item in sorted(ALLOWED_FILE_TYPES))
    return f"Unsupported file type: .{file_type or 'unknown'}. Allowed types: {allowed_types}"


def write_chunks_file(
    chunk_path: Path,
    document_id: str,
    source_name: str,
    file_type: str,
    chunks: list[TextChunk],
) -> None:
    # JSON 是调试产物；后续检索与追踪以 SQLite metadata 为事实源。
    payload = {
        "document_id": document_id,
        "source_name": source_name,
        "file_type": file_type,
        "chunk_count": len(chunks),
        "chunks": [chunk.__dict__ for chunk in chunks],
    }
    chunk_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_embeddings_and_index(db: Session, settings: Settings, chunks: list[Chunk]) -> None:
    embedding_client = DashScopeEmbeddingClient(settings)
    vector_store = FaissVectorStore(settings)

    texts = [chunk.text for chunk in chunks]
    vectors: list[list[float]] = []
    for batch in iter_batches(texts, settings.embedding_batch_size):
        vectors.extend(embedding_client.embed_texts(batch))

    # 当前 FAISS append 后再写 embedding metadata；后续 Question Trace 后应补 rebuild 校验。
    positions = vector_store.add_vectors(vectors)
    add_embeddings(
        db,
        chunk_positions=[
            (chunk.id, position)
            for chunk, position in zip(chunks, positions, strict=True)
        ],
        model_name=settings.embedding_model,
        vector_dim=settings.embedding_dim,
    )
