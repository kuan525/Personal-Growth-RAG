"""Question 用例：先检索 evidence，再基于 evidence 调 LLM 生成回答。"""

from sqlalchemy.orm import Session

from personal_growth_rag.application.retrieval.search_chunks import search_chunks
from personal_growth_rag.core.config import Settings
from personal_growth_rag.core.errors import QAError
from personal_growth_rag.domain.questions import NO_EVIDENCE_ANSWER, QuestionAnswer
from personal_growth_rag.infrastructure.llms.deepseek import DeepSeekLLMClient


def answer_question(
    question: str,
    top_k: int | None,
    settings: Settings,
    db: Session,
) -> QuestionAnswer:
    normalized_question = question.strip()
    if not normalized_question:
        raise QAError("question must not be empty")

    citations = search_chunks(normalized_question, top_k, settings, db)
    # 没有 evidence 时直接拒答，避免 LLM 用外部知识补全。
    if not citations:
        return QuestionAnswer(answer=NO_EVIDENCE_ANSWER, citations=[])

    llm_client = DeepSeekLLMClient(settings)
    answer = llm_client.answer_with_context(normalized_question, citations)
    return QuestionAnswer(answer=answer, citations=citations)
