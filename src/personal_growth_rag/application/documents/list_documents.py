from sqlalchemy.orm import Session

from personal_growth_rag.domain.documents import DocumentSummaryData
from personal_growth_rag.infrastructure.db.repositories.documents import (
    list_document_models,
    to_document_summary,
)


def list_documents(db: Session) -> list[DocumentSummaryData]:
    return [to_document_summary(document) for document in list_document_models(db)]
