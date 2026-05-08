from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_growth_rag.infrastructure.db.models import Embedding


def add_embeddings(
    db: Session,
    *,
    chunk_positions: list[tuple[str, int]],
    model_name: str,
    vector_dim: int,
) -> None:
    db.add_all(
        Embedding(
            chunk_id=chunk_id,
            model_name=model_name,
            vector_dim=vector_dim,
            index_position=position,
        )
        for chunk_id, position in chunk_positions
    )


def get_embeddings_by_positions(db: Session, positions: list[int]) -> dict[int, Embedding]:
    embeddings = db.scalars(select(Embedding).where(Embedding.index_position.in_(positions))).all()
    return {embedding.index_position: embedding for embedding in embeddings}
