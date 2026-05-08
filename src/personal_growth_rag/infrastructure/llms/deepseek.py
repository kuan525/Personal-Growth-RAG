import logging

from openai import OpenAI

from personal_growth_rag.core.config import Settings
from personal_growth_rag.core.errors import ProviderError
from personal_growth_rag.domain.prompts import SYSTEM_PROMPT, build_question_prompt
from personal_growth_rag.domain.questions import NO_EVIDENCE_ANSWER
from personal_growth_rag.domain.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class DeepSeekLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.deepseek_api_key:
            raise ProviderError("DEEPSEEK_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.llm_base_url)

    def answer_with_context(self, question: str, citations: list[RetrievedChunk]) -> str:
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_question_prompt(question, citations)},
            ],
            max_tokens=self.settings.llm_max_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )
        answer = response.choices[0].message.content
        if not answer or not answer.strip():
            logger.warning("DeepSeek returned an empty answer")
            return NO_EVIDENCE_ANSWER
        return answer.strip()
