from openai import OpenAI

from personal_growth_rag.core.config import Settings
from personal_growth_rag.core.errors import ProviderError


class DashScopeEmbeddingClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.dashscope_api_key:
            raise ProviderError("DASHSCOPE_API_KEY is not configured")
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.embedding_base_url,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
            dimensions=self.settings.embedding_dim,
        )
        vectors = [item.embedding for item in response.data]
        for vector in vectors:
            if len(vector) != self.settings.embedding_dim:
                raise ProviderError(
                    f"Embedding dimension mismatch: expected {self.settings.embedding_dim}, "
                    f"got {len(vector)}"
                )
        return vectors

    def embed_query(self, query_text: str) -> list[float]:
        return self.embed_texts([query_text])[0]
