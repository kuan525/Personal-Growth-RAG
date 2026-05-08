"""Document repository 只处理 SQLAlchemy 读写和 DB model -> domain data 转换。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_growth_rag.core.constants import DOCUMENT_STATUS_ACTIVE, DOCUMENT_STATUS_FAILED
from personal_growth_rag.domain.documents import DocumentDetailData, DocumentSummaryData
from personal_growth_rag.infrastructure.db.models import Document


def find_active_document_by_hash(db: Session, content_hash: str) -> Document | None:
    return db.scalar(
        select(Document).where(
            Document.content_hash == content_hash,
            Document.status == DOCUMENT_STATUS_ACTIVE,
        )
    )


def get_document_model(db: Session, document_id: str) -> Document | None:
    return db.get(Document, document_id)


def list_document_models(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


def add_document(db: Session, document: Document) -> None:
    db.add(document)


def mark_document_active(db: Session, document: Document, chunk_count: int) -> None:
    document.status = DOCUMENT_STATUS_ACTIVE
    document.chunk_count = chunk_count
    document.error_message = None


def mark_document_failed(db: Session, document_id: str, error_message: str) -> None:
    db.rollback()
    document = db.get(Document, document_id)
    if document is None:
        return
    document.status = DOCUMENT_STATUS_FAILED
    document.error_message = error_message
    db.commit()


def to_document_summary(document: Document) -> DocumentSummaryData:
    return DocumentSummaryData(
        document_id=document.id,
        source_name=document.source_name,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def to_document_detail(document: Document) -> DocumentDetailData:
    summary = to_document_summary(document)
    return DocumentDetailData(
        **summary.__dict__,
        stored_path=document.stored_path,
        chunk_path=document.chunk_path,
        error_message=document.error_message,
    )
