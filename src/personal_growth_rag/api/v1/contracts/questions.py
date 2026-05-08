"""Questions API request/response contracts。"""

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class CitationResponse(BaseModel):
    document_id: str
    source_name: str
    chunk_id: str
    chunk_order: int
    score: float
    text: str


class QuestionResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
