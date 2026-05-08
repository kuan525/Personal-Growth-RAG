import logging

from fastapi import FastAPI
from src.app.api.documents import router as documents_router
from src.app.api.questions import router as questions_router
from src.app.api.search import router as search_router
from src.app.common.logging import setup_logging
from src.app.config import get_settings
from src.app.storage.database import init_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)
    init_db(settings)

    app = FastAPI(title="Personal Growth RAG MVP")
    app.include_router(documents_router)
    app.include_router(search_router)
    app.include_router(questions_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        # health check 是 Step 1 的唯一功能，用来证明 API 服务已经能正常启动和响应。
        logger.info("Health check requested")
        return {"status": "ok"}

    return app


app = create_app()
