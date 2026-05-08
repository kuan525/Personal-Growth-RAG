"""SQLAlchemy engine/session 管理。

当前是本地单用户 SQLite；保留 session factory 方便 API、CLI 和后续 jobs 共享。
"""

from collections.abc import Generator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from personal_growth_rag.core.config import Settings, get_settings
from personal_growth_rag.infrastructure.db.base import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_database_url: str | None = None


def init_db(settings: Settings) -> None:
    engine = get_engine(settings)

    # 导入 models 让 SQLAlchemy 在 create_all 前完成 metadata 注册。
    from personal_growth_rag.infrastructure.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_engine(settings: Settings) -> Engine:
    global _database_url, _engine, _session_factory

    if _engine is not None and _database_url == settings.database_url:
        return _engine

    _ensure_sqlite_parent_dir(settings.database_url)
    connect_args = (
        {"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {}
    )
    _engine = create_engine(settings.database_url, connect_args=connect_args)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    _database_url = settings.database_url
    return _engine


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    get_engine(settings)
    if _session_factory is None:
        raise RuntimeError("Database session factory is not initialized")
    return _session_factory


def get_db_session(settings: Annotated[Settings, Depends(get_settings)]) -> Generator[Session]:
    session_factory = get_session_factory(settings)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    database_path = database_url.removeprefix(prefix)
    if database_path in {":memory:", ""}:
        return

    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
