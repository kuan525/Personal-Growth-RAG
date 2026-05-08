import logging

from fastapi import APIRouter

from personal_growth_rag.api.v1.contracts.common import ApiResponse, HealthData, ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse[HealthData])
def health() -> ApiResponse[HealthData]:
    logger.info("Health check requested")
    return ok(HealthData(status="ok"))
