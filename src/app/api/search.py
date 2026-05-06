import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.config import Settings, get_settings
from src.app.schemas.search import SearchRequest, SearchResponse
from src.app.search.service import SearchError, search_chunks
from src.app.storage.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    request: SearchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> SearchResponse:
    try:
        return search_chunks(request.query_text, request.top_k, settings, db)
    except SearchError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Search failed: error=%s", error)
        raise HTTPException(status_code=500, detail="Search failed") from error
