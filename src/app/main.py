import logging

from fastapi import FastAPI
from src.app.api.documents import router as documents_router
from src.app.common.logging import setup_logging
from src.app.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)

    app = FastAPI(title="Personal Growth RAG MVP")
    app.include_router(documents_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        # health check 是 Step 1 的唯一功能，用来证明 API 服务已经能正常启动和响应。
        logger.info("Health check requested")
        return {"status": "ok"}

    return app


app = create_app()
