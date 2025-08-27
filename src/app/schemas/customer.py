"""
Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import SecurityUtils


class CustomerBase(BaseModel):
    """Base customer schema with common fields"""
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v) > 100:
            raise ValueError('Name too long')
        
        v = SecurityUtils.sanitize_string(v)
        if not SecurityUtils.validate_name(v):
            raise ValueError('Name contains invalid characters')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not SecurityUtils.validate_phone(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError('Address too long')
        return SecurityUtils.sanitize_string(v) if v else v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name too long')
            
            v = SecurityUtils.sanitize_string(v)
            if not SecurityUtils.validate_name(v):
                raise ValueError('Name contains invalid characters')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v and not SecurityUtils.validate_phone(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if v and len(v) > 500:
                raise ValueError('Address too long')
            return SecurityUtils.sanitize_string(v) if v else v
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class CustomerResponse(CustomerBase):
    """Schema for customer responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    @field_validator('date_of_birth', mode='before')
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is None:
            return None
        if hasattr(v, 'strftime'):  # datetime.date or datetime.datetime
            return v.strftime('%Y-%m-%d')
        return str(v)


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: str
    service: str
    version: str
    database: str


class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str
