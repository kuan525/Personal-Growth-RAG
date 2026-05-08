import logging

from openai import OpenAI
from sqlalchemy.orm import Session
from src.app.config import Settings
from src.app.schemas.questions import Citation, QuestionResponse
from src.app.search.service import search_chunks

logger = logging.getLogger(__name__)


class QAError(RuntimeError):
    pass


NO_EVIDENCE_ANSWER = "现有资料不足以回答这个问题。"


SYSTEM_PROMPT = """你是 Personal Growth RAG 的问答助手。
你必须只基于用户提供的 context 回答问题，不要使用外部知识或猜测。
如果 context 不足以支持答案，必须明确说“现有资料不足以回答这个问题”。
回答要简洁、具体，并尽量在关键结论后标注引用编号，例如 [1]、[2]。
不要编造引用编号，不要编造文档来源。"""


def answer_question(
    question: str,
    top_k: int | None,
    settings: Settings,
    db: Session,
) -> QuestionResponse:
    normalized_question = question.strip()
    if not normalized_question:
        raise QAError("question must not be empty")

    search_response = search_chunks(normalized_question, top_k, settings, db)
    citations = [
        Citation(
            document_id=result.document_id,
            source_name=result.source_name,
            chunk_id=result.chunk_id,
            chunk_order=result.chunk_order,
            score=result.score,
            text=result.text,
        )
        for result in search_response.results
    ]
    if not citations:
        return QuestionResponse(answer=NO_EVIDENCE_ANSWER, citations=[])

    answer = _generate_answer(normalized_question, citations, settings)
    return QuestionResponse(answer=answer, citations=citations)


def _generate_answer(question: str, citations: list[Citation], settings: Settings) -> str:
    if not settings.deepseek_api_key:
        raise QAError("DEEPSEEK_API_KEY is not configured")

    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.llm_base_url)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(question, citations)},
        ],
        max_tokens=settings.llm_max_tokens,
        extra_body={"thinking": {"type": "disabled"}},
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        logger.warning("DeepSeek returned an empty answer")
        return NO_EVIDENCE_ANSWER
    return answer.strip()


def _build_user_prompt(question: str, citations: list[Citation]) -> str:
    context_blocks = []
    for index, citation in enumerate(citations, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] source_name={citation.source_name}",
                    f"document_id={citation.document_id}",
                    f"chunk_id={citation.chunk_id}",
                    f"chunk_order={citation.chunk_order}",
                    f"score={citation.score:.4f}",
                    "text:",
                    citation.text,
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks)
    return f"""问题：{question}

Context：
{context}

请基于上面的 Context 回答问题。"""
