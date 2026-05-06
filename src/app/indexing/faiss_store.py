from pathlib import Path

import faiss
import numpy as np
from src.app.config import Settings


class FaissIndexError(RuntimeError):
    pass


class FaissIndexStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index_path = Path(settings.faiss_index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index = self._load_or_create_index()

    @property
    def size(self) -> int:
        return int(self.index.ntotal)

    def add_vectors(self, vectors: list[list[float]]) -> list[int]:
        if not vectors:
            return []
        matrix = normalize_vectors(vectors, self.settings.embedding_dim)
        start_position = self.size
        self.index.add(matrix) # type: ignore
        self.save()
        return list(range(start_position, start_position + len(vectors)))

    def search(self, vector: list[float], top_k: int) -> list[tuple[int, float]]:
        if self.size == 0 or top_k <= 0:
            return []
        query = normalize_vectors([vector], self.settings.embedding_dim)
        search_k = min(top_k, self.size)
        scores, indices = self.index.search(query, search_k) # type: ignore
        results: list[tuple[int, float]] = []
        for index_position, score in zip(indices[0], scores[0], strict=False):
            if index_position < 0:
                continue
            results.append((int(index_position), float(score)))
        return results

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))

    def _load_or_create_index(self) -> faiss.Index:
        if not self.index_path.exists():
            return faiss.IndexFlatIP(self.settings.embedding_dim)

        index = faiss.read_index(str(self.index_path))
        if index.d != self.settings.embedding_dim:
            raise FaissIndexError(
                f"FAISS index dimension mismatch: expected {self.settings.embedding_dim}, "
                f"got {index.d}. Rebuild the index or adjust EMBEDDING_DIM."
            )
        return index


def normalize_vectors(vectors: list[list[float]], expected_dim: int) -> np.ndarray:
    matrix = np.asarray(vectors, dtype="float32")
    if matrix.ndim != 2 or matrix.shape[1] != expected_dim:
        raise FaissIndexError(
            f"Vector dimension mismatch: expected {expected_dim}, got {matrix.shape}"
        )
    faiss.normalize_L2(matrix)
    return matrix
