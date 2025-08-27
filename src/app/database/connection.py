"""
Database connection manager with support for both traditional and IAM authentication.

This module demonstrates the evolution from username/password to IAM authentication:
1. Traditional: Uses static username/password (security risk)
2. IAM: Uses temporary tokens generated from IAM credentials (secure)
"""

import os
import boto3
import pymysql
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Enhanced database manager supporting both traditional and IAM authentication"""

    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", 3306))
        self.db_name = os.getenv("DB_NAME", "inscribe_customers")
        self.db_user = os.getenv("DB_USER", "admin")
        self.db_password = os.getenv("DB_PASSWORD", "password")

        # IAM Authentication settings
        self.use_iam_auth = os.getenv("USE_IAM_AUTH", "false").lower() == "true"
        self.iam_db_user = os.getenv("IAM_DB_USER", "iam_app_user")
        self.aws_region = os.getenv("AWS_REGION", "eu-west-1")

        # Initialize RDS client for IAM tokens (only if IAM auth is enabled)
        if self.use_iam_auth:
            self.rds_client = boto3.client("rds", region_name=self.aws_region)

        self._initialize_database_with_retry()

    def _get_connection_config(self) -> Dict[str, Any]:
        """Get database connection configuration based on authentication method"""

        base_config = {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "charset": "utf8mb4",
            "autocommit": True,
        }

        if self.use_iam_auth:
            # IAM Authentication: Generate temporary token
            logger.info("Using IAM database authentication")
            token = self._generate_iam_token()

            config = {
                **base_config,
                "user": self.iam_db_user,
                "password": token,
                "ssl": {
                    "ssl_ca": "/opt/amazon-rds-ca-cert.pem"
                },  # Required for IAM auth
                "ssl_disabled": False,
                "connect_timeout": 60,
            }
        else:
            # Traditional Authentication: Static username/password
            logger.info("Using traditional username/password authentication")
            config = {**base_config, "user": self.db_user, "password": self.db_password}

        return config

    def _generate_iam_token(self) -> str:
        """Generate IAM authentication token for RDS"""
        try:
            # Generate token valid for 15 minutes
            token = self.rds_client.generate_db_auth_token(
                DBHostname=self.db_host,
                Port=self.db_port,
                DBUsername=self.iam_db_user,
                Region=self.aws_region,
            )
            logger.debug("IAM authentication token generated successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to generate IAM authentication token: {e}")
            raise

    def _initialize_database_with_retry(self, max_retries=10, delay=5):
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
                    logger.error("Max database connection retries reached.")
                    raise

    def _test_connection(self):
        """Test database connection"""
        try:
            config = self._get_connection_config()
            connection = pymysql.connect(**config)
            connection.close()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _initialize_database(self):
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
    def get_connection(self):
        """Get database connection with proper error handling and cleanup"""
        connection = None
        try:
            config = self._get_connection_config()
            connection = pymysql.connect(**config)
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()


# For comparison, here's how the authentication methods differ:


class TraditionalAuth:
    """Traditional username/password authentication (less secure)"""

    def get_config(self):
        return {
            "host": "my-rds-instance.amazonaws.com",
            "user": "dbadmin",
            "password": "MySecretPassword123!",  # Static password - security risk!
            "database": "myapp",
        }

    # Issues with this approach:
    # - Password stored in environment variables or code
    # - No automatic rotation
    # - Long-lived credentials
    # - Risk of exposure in logs/memory dumps


class IAMAuth:
    """IAM token-based authentication (more secure)"""

    def __init__(self):
        self.rds_client = boto3.client("rds")

    def get_config(self):
        # Generate short-lived token (15 minutes)
        token = self.rds_client.generate_db_auth_token(
            DBHostname="my-rds-instance.amazonaws.com",
            Port=3306,
            DBUsername="iam_app_user",
            Region="eu-west-1",
        )

        return {
            "host": "my-rds-instance.amazonaws.com",
            "user": "iam_app_user",
            "password": token,  # Temporary token, expires in 15 minutes
            "database": "myapp",
            "ssl": {"ssl_ca": "/opt/amazon-rds-ca-cert.pem"},
        }

    # Benefits of this approach:
    # - No static passwords
    # - Automatic token expiration (15 minutes)
    # - Uses IAM roles for authentication
    # - Centralized access control through IAM
    # - Audit trail through CloudTrail


# Usage example for deployment configuration:
def get_database_manager():
    """Factory function to get appropriate database manager"""
    use_iam = os.getenv("USE_IAM_AUTH", "false").lower() == "true"

    if use_iam:
        logger.info("Initializing database with IAM authentication")
        return DatabaseConnection()  # Will use IAM auth based on environment
    else:
        logger.info("Initializing database with traditional authentication")
        return DatabaseConnection()  # Will use username/password


# Environment variable examples:
# Traditional auth:
# DB_HOST=my-rds.amazonaws.com
# DB_USER=dbadmin
# DB_PASSWORD=secret123
# USE_IAM_AUTH=false

# IAM auth:
# DB_HOST=my-rds.amazonaws.com
# IAM_DB_USER=iam_app_user
# USE_IAM_AUTH=true
# AWS_REGION=eu-west-1
# (No DB_PASSWORD needed!)

# Benefits of this approach:
# - No static passwords
# - Automatic token expiration (15 minutes)
# - Uses IAM roles for authentication
# - Centralized access control through IAM
# - Audit trail through CloudTrail


# Usage example for deployment configuration:
def get_database_manager():
    """Factory function to get appropriate database manager"""
    use_iam = os.getenv("USE_IAM_AUTH", "false").lower() == "true"

    if use_iam:
        logger.info("Initializing database with IAM authentication")
        return DatabaseConnection()  # Will use IAM auth based on environment
    else:
        logger.info("Initializing database with traditional authentication")
        return DatabaseConnection()  # Will use username/password


# Environment variable examples:
# Traditional auth:
# DB_HOST=my-rds.amazonaws.com
# DB_USER=dbadmin
# DB_PASSWORD=secret123
# USE_IAM_AUTH=false

# IAM auth:
# DB_HOST=my-rds.amazonaws.com
# IAM_DB_USER=iam_app_user
# USE_IAM_AUTH=true
# AWS_REGION=eu-west-1
# (No DB_PASSWORD needed!)
