from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query_text: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SearchResult(BaseModel):
    document_id: str
    source_name: str
    chunk_id: str
    chunk_order: int
    score: float
    text: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
