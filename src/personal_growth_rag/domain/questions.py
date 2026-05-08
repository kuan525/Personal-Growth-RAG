from dataclasses import dataclass

from personal_growth_rag.domain.retrieval import RetrievedChunk

NO_EVIDENCE_ANSWER = "现有资料不足以回答这个问题。"


@dataclass(frozen=True)
class QuestionAnswer:
    answer: str
    citations: list[RetrievedChunk]
