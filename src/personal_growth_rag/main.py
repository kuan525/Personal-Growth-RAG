from fastapi import FastAPI

from personal_growth_rag.api.v1.router import api_router, register_exception_handlers
from personal_growth_rag.core.config import get_settings
from personal_growth_rag.core.logging import setup_logging
from personal_growth_rag.infrastructure.db.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)
    init_db(settings)

    app = FastAPI(title="Personal Growth RAG MVP")
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
