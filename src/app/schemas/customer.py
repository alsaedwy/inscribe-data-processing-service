"""
Pydantic schemas for request/response validation.

This module defines Pydantic schemas for the Inscribe Customer Data Service,
providing comprehensive data validation, serialization, and documentation
for all customer-related API operations.

The schemas include:
- Input validation with security sanitization
- Field-level validators for data integrity
- Type conversion and format validation
- Comprehensive error messages for validation failures
- Security measures against injection attacks

Key Features:
- Email validation using EmailStr
- Phone number format validation
- Name sanitization to prevent malicious input
- Date format validation (YYYY-MM-DD)
- Length limits on all text fields
- SQL injection prevention through input sanitization

Example:
    ```python
    from app.schemas.customer import CustomerCreate, CustomerResponse

    # Create schema with validation
    customer_data = CustomerCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1-555-0123",
        date_of_birth="1990-01-01"
    )

    # Response schema automatically formats data
    response = CustomerResponse(
        id=1,
        first_name=customer_data.first_name,
        # ... other fields
    )
    ```

Security Features:
- String sanitization to prevent XSS attacks
- Input length validation to prevent buffer overflows
- Character validation for names and phone numbers
- Email format validation with domain checking
- Date format validation to prevent injection

Note:
    All validation errors include descriptive messages to help API clients
    understand and correct invalid input data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import SecurityUtils


class CustomerBase(BaseModel):
    """
    Base customer schema with common fields.

    This base class defines the common fields shared across all customer
    schemas (create, update, response). It includes core customer attributes
    with appropriate types and optional field designations.

    Attributes:
        first_name (str): Customer's first name (required)
        last_name (str): Customer's last name (required)
        email (EmailStr): Customer's email address with validation (required)
        phone (Optional[str]): Customer's phone number (optional)
        address (Optional[str]): Customer's physical address (optional)
        date_of_birth (Optional[str]): Customer's birth date in YYYY-MM-DD format (optional)

    Note:
        This class is not used directly but serves as a base for other schemas
        to ensure consistency across create, update, and response operations.
    """

    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format


class CustomerCreate(CustomerBase):
    """
    Schema for creating a new customer.

    This schema extends CustomerBase with comprehensive validation rules
    for creating new customer records. It includes field-level validators
    that sanitize input, check for malicious content, and enforce business
    rules for data integrity and security.

    Validation Rules:
        - Names: Non-empty, max 100 chars, sanitized, valid characters only
        - Phone: Optional, format validation if provided
        - Address: Optional, max 500 chars, sanitized if provided
        - Date of birth: Optional, must be in YYYY-MM-DD format if provided
        - Email: Automatic validation through EmailStr type

    Example:
        ```python
        customer = CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-0123",
            address="123 Main Street, City, State 12345",
            date_of_birth="1990-01-01"
        )
        ```

    Raises:
        ValueError: For invalid input data with descriptive error messages

    Note:
        All string fields are automatically sanitized to prevent XSS attacks
        and other security vulnerabilities through the SecurityUtils module.
    """

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate and sanitize name fields.

        Args:
            v (str): The name value to validate

        Returns:
            str: Sanitized and validated name

        Raises:
            ValueError: If name is empty, too long, or contains invalid characters
        """
        if not v or len(v.strip()) < 1:
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name too long")

        v = SecurityUtils.sanitize_string(v)
        if not SecurityUtils.validate_name(v):
            raise ValueError("Name contains invalid characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate phone number format.

        Args:
            v (Optional[str]): Phone number to validate

        Returns:
            Optional[str]: Validated phone number or None

        Raises:
            ValueError: If phone number format is invalid
        """
        if v and not SecurityUtils.validate_phone(v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize address field.

        Args:
            v (Optional[str]): Address to validate

        Returns:
            Optional[str]: Sanitized address or None

        Raises:
            ValueError: If address is too long
        """
        if v and len(v) > 500:
            raise ValueError("Address too long")
        return SecurityUtils.sanitize_string(v) if v else v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate date of birth format.

        Args:
            v (Optional[str]): Date of birth in YYYY-MM-DD format

        Returns:
            Optional[str]: Validated date string or None

        Raises:
            ValueError: If date format is invalid
        """
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) < 1:
                raise ValueError("Name cannot be empty")
            if len(v) > 100:
                raise ValueError("Name too long")

            v = SecurityUtils.sanitize_string(v)
            if not SecurityUtils.validate_name(v):
                raise ValueError("Name contains invalid characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v and not SecurityUtils.validate_phone(v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if v and len(v) > 500:
                raise ValueError("Address too long")
            return SecurityUtils.sanitize_string(v) if v else v
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v


class CustomerResponse(CustomerBase):
    """Schema for customer responses"""

    id: int
    created_at: datetime
    updated_at: datetime

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is None:
            return None
        if hasattr(v, "strftime"):  # datetime.date or datetime.datetime
            return v.strftime("%Y-%m-%d")
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
