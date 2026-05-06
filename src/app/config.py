from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 当前先保留本地优先 MVP 需要的配置；LLM、Graph 等配置后续步骤再加。
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    data_dir: str = Field(default="data", alias="DATA_DIR")
    upload_dir_name: str = Field(default="uploads", alias="UPLOAD_DIR_NAME")
    chunk_dir_name: str = Field(default="chunks", alias="CHUNK_DIR_NAME")
    chunk_size: int = Field(default=200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=30, alias="CHUNK_OVERLAP")
    database_url: str = Field(default="sqlite:///data/app.db", alias="DATABASE_URL")
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    embedding_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="EMBEDDING_BASE_URL",
    )
    embedding_model: str = Field(default="text-embedding-v4", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    embedding_batch_size: int = Field(default=10, alias="EMBEDDING_BATCH_SIZE")
    faiss_index_path: str = Field(default="data/indexes/chunks.faiss", alias="FAISS_INDEX_PATH")
    search_top_k: int = Field(default=5, alias="SEARCH_TOP_K")


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    # 使用缓存是为了避免每次请求都重新解析环境变量；后续测试如需覆盖可清理 cache。
    return Settings()
