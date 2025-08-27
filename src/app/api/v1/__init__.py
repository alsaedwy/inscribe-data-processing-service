"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1 import customers, health

api_router = APIRouter(prefix="/api/v1")

# Include all v1 routes
api_router.include_router(health.router)
api_router.include_router(customers.router)
