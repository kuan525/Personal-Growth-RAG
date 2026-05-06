from openai import OpenAI
from src.app.config import Settings


class EmbeddingError(RuntimeError):
    pass


class DashScopeEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.dashscope_api_key:
            raise EmbeddingError("DASHSCOPE_API_KEY is not configured")
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
                raise EmbeddingError(
                    f"Embedding dimension mismatch: expected {self.settings.embedding_dim}, "
                    f"got {len(vector)}"
                )
        return vectors

    def embed_query(self, query_text: str) -> list[float]:
        return self.embed_texts([query_text])[0]


def iter_batches(items: list[str], batch_size: int) -> list[list[str]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]
