from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from personal_growth_rag.api.v1.contracts.common import ApiResponse, ok
from personal_growth_rag.api.v1.contracts.search import (
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
)
from personal_growth_rag.api.v1.deps import Settings, get_db_session, get_settings
from personal_growth_rag.application.retrieval.search_chunks import search_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=ApiResponse[SearchResponse])
def search(
    request: SearchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> ApiResponse[SearchResponse]:
    results = search_chunks(request.query_text, request.top_k, settings, db)
    data = SearchResponse(results=[SearchResultResponse(**result.__dict__) for result in results])
    return ok(data)
