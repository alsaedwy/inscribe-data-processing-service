"""
Health check endpoints
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.schemas.customer import HealthResponse
from app.services.customer_service import CustomerService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        database_healthy = CustomerService.check_database_health()

        if not database_healthy:
            logger.error("Health check failed: database not accessible")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy - database connection failed",
            )

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            service=settings.app_name,
            version=settings.version,
            database="connected",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )
