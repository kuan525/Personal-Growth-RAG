from sqlalchemy import select
from sqlalchemy.orm import Session
from src.app.config import Settings
from src.app.embeddings.service import DashScopeEmbeddingService
from src.app.indexing.faiss_store import FaissIndexStore
from src.app.schemas.search import SearchResponse, SearchResult
from src.app.storage.models import Chunk, Document, Embedding


class SearchError(ValueError):
    pass


def search_chunks(
    request_query: str, top_k: int | None, settings: Settings, db: Session
) -> SearchResponse:
    query_text = request_query.strip()
    if not query_text:
        raise SearchError("query_text must not be empty")

    requested_top_k = top_k or settings.search_top_k
    requested_top_k = min(max(requested_top_k, 1), 20)

    faiss_store = FaissIndexStore(settings)
    if faiss_store.size == 0:
        return SearchResponse(results=[])

    embedding_service = DashScopeEmbeddingService(settings)
    query_vector = embedding_service.embed_query(query_text)
    hits = faiss_store.search(query_vector, requested_top_k)
    if not hits:
        return SearchResponse(results=[])

    positions = [position for position, _score in hits]
    embeddings = db.scalars(
        select(Embedding).where(Embedding.index_position.in_(positions))
    ).all()
    embedding_by_position = {embedding.index_position: embedding for embedding in embeddings}

    results: list[SearchResult] = []
    for position, score in hits:
        embedding = embedding_by_position.get(position)
        if embedding is None:
            continue
        chunk = db.get(Chunk, embedding.chunk_id)
        if chunk is None:
            continue
        document = db.get(Document, chunk.document_id)
        if document is None or document.status != "active":
            continue
        results.append(
            SearchResult(
                document_id=document.id,
                source_name=document.source_name,
                chunk_id=chunk.id,
                chunk_order=chunk.chunk_order,
                score=score,
                text=chunk.text,
            )
        )

    return SearchResponse(results=results)
