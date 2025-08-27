"""
Customer API endpoints
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.core.security import authenticate
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
    MessageResponse,
)
from app.services.customer_service import CustomerService

logger = get_logger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate, username: str = Depends(authenticate)
):
    """Create a new customer with proper input validation and SQL injection prevention"""
    try:
        result = CustomerService.create_customer(customer)
        return CustomerResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
                if "email already exists" in str(e)
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error creating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0, limit: int = 100, username: str = Depends(authenticate)
):
    """Get all customers with pagination"""
    try:
        results = CustomerService.get_customers(skip=skip, limit=limit)
        return [CustomerResponse(**customer) for customer in results]
    except Exception as e:
        logger.error(f"Error retrieving customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, username: str = Depends(authenticate)):
    """Get a specific customer by ID"""
    try:
        result = CustomerService.get_customer_by_id(customer_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )
        return CustomerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    username: str = Depends(authenticate),
):
    """Update a customer"""
    try:
        result = CustomerService.update_customer(customer_id, customer_update)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )
        return CustomerResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
                if "email already exists" in str(e)
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{customer_id}", response_model=MessageResponse)
async def delete_customer(customer_id: int, username: str = Depends(authenticate)):
    """Delete a customer"""
    try:
        success = CustomerService.delete_customer(customer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )
        return MessageResponse(message="Customer deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
