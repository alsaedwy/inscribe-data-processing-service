"""
Authentication and security utilities
"""

import secrets
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Basic authentication dependency

    In production, replace with proper OAuth2/JWT authentication
    """
    # Get credentials from settings (which handles Secrets Manager or env vars)
    expected_username, expected_password = settings.get_api_credentials()

    correct_username = secrets.compare_digest(credentials.username, expected_username)
    correct_password = secrets.compare_digest(credentials.password, expected_password)

    if not (correct_username and correct_password):
        logger.warning(f"Authentication failed for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info(f"User authenticated successfully: {credentials.username}")
    return credentials.username


class SecurityUtils:
    """Security utility functions"""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Basic string sanitization"""
        if not value:
            return value
        return value.strip()

    @staticmethod
    def validate_name(value: str) -> bool:
        """Validate name field contains only allowed characters"""
        if not value:
            return False

        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'")
        return all(c in allowed_chars for c in value)

    @staticmethod
    def validate_phone(value: str) -> bool:
        """Validate phone number format"""
        if not value:
            return True  # Optional field

        cleaned = "".join(c for c in value if c.isdigit())
        return 7 <= len(cleaned) <= 15
