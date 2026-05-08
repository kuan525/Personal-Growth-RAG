from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from personal_growth_rag.api.v1.contracts.common import ApiResponse, ok
from personal_growth_rag.api.v1.contracts.questions import (
    CitationResponse,
    QuestionRequest,
    QuestionResponse,
)
from personal_growth_rag.api.v1.deps import Settings, get_db_session, get_settings
from personal_growth_rag.application.questions.answer_question import answer_question

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=ApiResponse[QuestionResponse])
def ask_question(
    request: QuestionRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db_session)],
) -> ApiResponse[QuestionResponse]:
    result = answer_question(request.question, request.top_k, settings, db)
    data = QuestionResponse(
        answer=result.answer,
        citations=[CitationResponse(**citation.__dict__) for citation in result.citations],
    )
    return ok(data)
