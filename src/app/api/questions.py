import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.config import Settings, get_settings
from src.app.qa.service import QAError, answer_question
from src.app.schemas.questions import QuestionRequest, QuestionResponse
from src.app.search.service import SearchError
from src.app.storage.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionResponse)
def ask_question(
    request: QuestionRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> QuestionResponse:
    try:
        return answer_question(request.question, request.top_k, settings, db)
    except (QAError, SearchError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Question answering failed: error=%s", error)
        raise HTTPException(status_code=500, detail="Question answering failed") from error
