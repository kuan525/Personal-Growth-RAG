import logging

from src.app.config import Settings

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(settings: Settings) -> None:
    # Step 1 先用标准库 logging，足够支撑启动、health check 和后续小步调试。
    logging.basicConfig(level=settings.log_level.upper(), format=LOG_FORMAT)
