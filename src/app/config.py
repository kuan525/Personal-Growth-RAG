from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Step 1 只保留服务启动必需配置；数据库、OpenRouter、FAISS 等配置后续步骤再加。
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(extra="ignore")


@lru_cache
def get_settings() -> Settings:
    # 使用缓存是为了避免每次请求都重新解析环境变量；后续测试如需覆盖可清理 cache。
    return Settings()
