"""
Database connection and management with IAM authentication support
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Generator

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import settings
from app.core.logging import get_logger

# Import boto3 for IAM authentication if available
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

logger = get_logger(__name__)


class DatabaseManager:
    """Secure database manager with connection pooling and IAM authentication support"""

    def __init__(self):
        self.use_iam_auth = settings.use_iam_auth
        self.base_config = settings.database_config

        # Initialize RDS client for IAM token generation if needed
        if self.use_iam_auth and BOTO3_AVAILABLE:
            self.rds_client = boto3.client("rds", region_name=settings.aws_region)
            logger.info("IAM database authentication enabled")
        elif self.use_iam_auth and not BOTO3_AVAILABLE:
            logger.error("IAM authentication requested but boto3 not available")
            raise ImportError("boto3 is required for IAM database authentication")
        else:
            self.rds_client = None
            logger.info("Using traditional database authentication")

        self._initialize_database_with_retry()

    def _generate_iam_token(self) -> str:
        """Generate IAM authentication token for RDS"""
        if not self.rds_client:
            raise RuntimeError("RDS client not initialized for IAM authentication")

        try:
            # Generate token valid for 15 minutes
            token = self.rds_client.generate_db_auth_token(
                DBHostname=settings.db_host,
                Port=settings.db_port,
                DBUsername=settings.iam_db_user,
                Region=settings.aws_region,
            )
            logger.debug("IAM authentication token generated successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to generate IAM authentication token: {e}")
            raise

    def _get_connection_config(self) -> Dict[str, Any]:
        """Get database connection configuration with authentication"""
        config = self.base_config.copy()

        if self.use_iam_auth:
            # Generate fresh IAM token for each connection
            token = self._generate_iam_token()
            config.update(
                {
                    "password": token,
                    "ssl": {"ssl_ca": "/opt/amazon-rds-ca-cert.pem"},
                    "ssl_disabled": False,
                }
            )

        return config

    def _initialize_database_with_retry(
        self, max_retries: int = 10, delay: int = 5
    ) -> None:
        """Initialize database with retry logic for container startup"""
        for attempt in range(max_retries):
            try:
                self._test_connection()
                self._initialize_database()
                logger.info(f"Database connection established on attempt {attempt + 1}")
                return
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(
                        "Max database connection retries reached. "
                        "Starting without database connection."
                    )
                    # Don't raise exception - let the app start and handle DB errors per request

    def _test_connection(self) -> None:
        """Test database connection"""
        try:
            config = self._get_connection_config()
            connection = pymysql.connect(**config)
            connection.close()
            auth_method = "IAM" if self.use_iam_auth else "username/password"
            logger.info(
                f"Database connection test successful using {auth_method} authentication"
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _initialize_database(self) -> None:
        """Initialize database tables"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            phone VARCHAR(20),
            address TEXT,
            date_of_birth DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_last_name (last_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(create_table_sql)
                    logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    @contextmanager
    def get_connection(self) -> Generator[pymysql.Connection, None, None]:
        """Get database connection with automatic cleanup and IAM token refresh"""
        connection = None
        try:
            config = self._get_connection_config()
            connection = pymysql.connect(**config)
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if connection:
                connection.close()

    @contextmanager
    def get_cursor(
        self, dictionary: bool = True
    ) -> Generator[pymysql.cursors.Cursor, None, None]:
        """Get database cursor with automatic connection management"""
        with self.get_connection() as connection:
            cursor_class = DictCursor if dictionary else pymysql.cursors.Cursor
            with connection.cursor(cursor_class) as cursor:
                yield cursor

    @classmethod
    async def initialize(cls) -> None:
        """Async initialization for compatibility with application lifecycle"""
        # The initialization is already handled in __init__, but this method
        # provides compatibility with async application startup
        logger.info("Database manager initialized")

    @classmethod
    async def close(cls) -> None:
        """Async cleanup for compatibility with application lifecycle"""
        # No persistent connections to close in this implementation
        logger.info("Database manager cleanup completed")


# Global database manager instance
db_manager = DatabaseManager()
