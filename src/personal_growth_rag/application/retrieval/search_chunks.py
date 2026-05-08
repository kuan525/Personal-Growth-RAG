"""Retrieval 用例：query -> embedding -> FAISS -> SQLite hydrate -> evidence chunks。

它是 /search、/questions、后续 evaluation/memory/decision support 共享的证据检索层。
"""

from sqlalchemy.orm import Session

from personal_growth_rag.core.config import Settings
from personal_growth_rag.core.constants import DOCUMENT_STATUS_ACTIVE
from personal_growth_rag.core.errors import SearchError
from personal_growth_rag.domain.retrieval import RetrievedChunk
from personal_growth_rag.infrastructure.db.models import Chunk, Document
from personal_growth_rag.infrastructure.db.repositories.embeddings import (
    get_embeddings_by_positions,
)
from personal_growth_rag.infrastructure.embeddings.dashscope import DashScopeEmbeddingClient
from personal_growth_rag.infrastructure.vectorstores.faiss_store import FaissVectorStore


def search_chunks(
    request_query: str,
    top_k: int | None,
    settings: Settings,
    db: Session,
) -> list[RetrievedChunk]:
    query_text = request_query.strip()
    if not query_text:
        raise SearchError("query_text must not be empty")

    requested_top_k = top_k or settings.search_top_k
    requested_top_k = min(max(requested_top_k, 1), 20)

    vector_store = FaissVectorStore(settings)
    if vector_store.size == 0:
        return []

    embedding_client = DashScopeEmbeddingClient(settings)
    query_vector = embedding_client.embed_query(query_text)
    hits = vector_store.search(query_vector, requested_top_k)
    if not hits:
        return []

    positions = [position for position, _score in hits]
    embedding_by_position = get_embeddings_by_positions(db, positions)

    # 用 SQLite 反查 chunk/document，并过滤已失效文档；这样 FAISS 可作为派生索引重建。
    results: list[RetrievedChunk] = []
    for position, score in hits:
        embedding = embedding_by_position.get(position)
        if embedding is None:
            continue
        chunk = db.get(Chunk, embedding.chunk_id)
        if chunk is None:
            continue
        document = db.get(Document, chunk.document_id)
        if document is None or document.status != DOCUMENT_STATUS_ACTIVE:
            continue
        results.append(
            RetrievedChunk(
                document_id=document.id,
                source_name=document.source_name,
                chunk_id=chunk.id,
                chunk_order=chunk.chunk_order,
                score=score,
                text=chunk.text,
            )
        )

    return results
