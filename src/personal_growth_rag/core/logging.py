import logging

from personal_growth_rag.core.config import Settings

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(settings: Settings) -> None:
    # 当前保持轻量 logging；后续 question trace / evaluation 需要请求级观测时，
    # 再引入结构化日志和 request_id 贯穿。
    logging.basicConfig(level=settings.log_level.upper(), format=LOG_FORMAT)
