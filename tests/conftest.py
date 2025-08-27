"""
Pytest configuration and fixtures for the test suite
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Set test environment variables before any imports
os.environ["ENVIRONMENT"] = (
    "development"  # Use 'development' as it's allowed by the validator
)
os.environ["BASIC_AUTH_USERNAME"] = "test_user"
os.environ["BASIC_AUTH_PASSWORD"] = "test_password"
os.environ["USE_SECRETS_MANAGER"] = "false"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_NAME"] = "test_db"
os.environ["DB_USER"] = "test_user"
os.environ["DB_PASSWORD"] = "test_pass"


@pytest.fixture(autouse=True)
def mock_secrets_manager():
    """Mock secrets manager to avoid import issues"""
    with patch(
        "app.core.secrets.get_secrets_manager",
        side_effect=ImportError("Mocked secrets manager"),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests to avoid environment dependencies"""
    mock_settings = MagicMock()
    mock_settings.app_name = "Inscribe Customer Data Service"
    mock_settings.version = "1.0.0"
    mock_settings.environment = "test"
    mock_settings.is_development = True
    mock_settings.is_production = False
    mock_settings.cors_origins = ["*"]
    mock_settings.use_secrets_manager = False
    mock_settings.use_iam_auth = False
    mock_settings.datadog_enabled = False

    # Set the basic auth credentials that the fallback will use
    mock_settings.basic_auth_username = "test_user"
    mock_settings.basic_auth_password = "test_password"

    # Mock the get_api_credentials method directly
    mock_settings.get_api_credentials.return_value = ("test_user", "test_password")

    mock_settings.database_config = {
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass",
        "charset": "utf8mb4",
        "autocommit": True,
    }

    with patch("app.core.config.settings", mock_settings):
        yield mock_settings


@pytest.fixture(autouse=True)
def mock_database_setup():
    """Mock database setup to avoid actual database dependencies"""
    with patch("app.core.db_setup.run_database_setup", return_value=True):
        with patch("app.core.secure_credentials.load_credentials_at_startup"):
            yield


@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging setup to avoid file dependencies"""
    with patch("app.core.logging.setup_logging"):
        with patch("app.core.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            yield mock_logger


@pytest.fixture(autouse=True)
def mock_database_manager():
    """Mock database manager initialization to avoid database dependencies"""
    with patch("app.database.manager.DatabaseManager._initialize_database_with_retry"):
        with patch("app.database.manager.DatabaseManager._test_connection"):
            with patch("app.database.manager.DatabaseManager._initialize_database"):
                yield
