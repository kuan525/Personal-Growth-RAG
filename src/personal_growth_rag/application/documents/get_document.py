from sqlalchemy.orm import Session

from personal_growth_rag.core.errors import DocumentNotFoundError
from personal_growth_rag.domain.documents import DocumentDetailData
from personal_growth_rag.infrastructure.db.repositories.documents import (
    get_document_model,
    to_document_detail,
)


def get_document(document_id: str, db: Session) -> DocumentDetailData:
    document = get_document_model(db, document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")
    return to_document_detail(document)
