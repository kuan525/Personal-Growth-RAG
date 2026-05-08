from pathlib import Path

from personal_growth_rag.core.config import Settings


def upload_dir(settings: Settings) -> Path:
    return Path(settings.data_dir) / settings.upload_dir_name


def chunk_dir(settings: Settings) -> Path:
    return Path(settings.data_dir) / settings.chunk_dir_name
