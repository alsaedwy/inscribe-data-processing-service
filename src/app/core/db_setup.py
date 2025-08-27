"""
Database setup utilities for IAM authentication.
This module handles the creation of IAM database users on first startup.
"""

import logging
import os

import pymysql

logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles database setup for IAM authentication."""

    def __init__(self):
        self.master_host = os.getenv("DB_HOST")
        self.master_port = int(os.getenv("DB_PORT", 3306))
        self.master_username = os.getenv("DB_USER")
        self.master_password = os.getenv("DB_PASSWORD")
        self.database_name = os.getenv("DB_NAME")
        self.iam_username = os.getenv("IAM_DB_USERNAME", "iam_app_user")

    def create_iam_user(self) -> bool:
        """
        Create IAM database user if it doesn't exist.

        Returns:
            bool: True if user was created or already exists, False if failed
        """
        if not all(
            [
                self.master_host,
                self.master_username,
                self.master_password,
                self.database_name,
            ]
        ):
            logger.error("Missing required database connection parameters")
            return False

        try:
            # Connect using master credentials
            connection = pymysql.connect(
                host=self.master_host,
                port=self.master_port,
                user=self.master_username,
                password=self.master_password,
                database=self.database_name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=30,
            )

            with connection:
                with connection.cursor() as cursor:
                    # Check if IAM user already exists
                    cursor.execute(
                        "SELECT User FROM mysql.user WHERE User = %s AND Host = '%'",
                        (self.iam_username,),
                    )

                    if cursor.fetchone():
                        logger.info(f"IAM database user '{self.iam_username}' already exists")
                        return True

                    # Create IAM user
                    logger.info(f"Creating IAM database user '{self.iam_username}'")

                    # Create user with AWS IAM authentication
                    cursor.execute(
                        f"CREATE USER '{self.iam_username}'@'%' "
                        f"IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS'"
                    )

                    # Grant necessary permissions
                    cursor.execute(
                        f"GRANT SELECT, INSERT, UPDATE, DELETE ON "
                        f"{self.database_name}.* TO '{self.iam_username}'@'%'"
                    )

                    # Flush privileges
                    cursor.execute("FLUSH PRIVILEGES")

                    connection.commit()
                    logger.info(f"Successfully created IAM database user " f"'{self.iam_username}'")
                    return True

        except pymysql.Error as e:
            logger.error(f"Database error while creating IAM user: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while creating IAM user: {e}")
            return False

    def setup_database_schema(self) -> bool:
        """
        Set up the database schema (tables, etc.) if needed.

        Returns:
            bool: True if schema setup was successful
        """
        try:
            connection = pymysql.connect(
                host=self.master_host,
                port=self.master_port,
                user=self.master_username,
                password=self.master_password,
                database=self.database_name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=30,
            )

            with connection:
                with connection.cursor() as cursor:
                    # Check if customers table exists
                    cursor.execute(
                        """
                        SELECT COUNT(*) as count
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = 'customers'
                    """,
                        (self.database_name,),
                    )

                    result = cursor.fetchone()
                    if result and result["count"] > 0:
                        logger.info("Database schema already exists")
                        return True

                    # Create customers table
                    logger.info("Creating customers table")
                    cursor.execute(
                        """
                        CREATE TABLE customers (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            first_name VARCHAR(100) NOT NULL,
                            last_name VARCHAR(100) NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            phone VARCHAR(20),
                            address TEXT,
                            date_of_birth DATE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
                            INDEX idx_email (email),
                            INDEX idx_name (last_name, first_name)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                        COLLATE=utf8mb4_unicode_ci
                    """
                    )

                    connection.commit()
                    logger.info("Successfully created database schema")
                    return True

        except pymysql.Error as e:
            logger.error(f"Database error while setting up schema: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while setting up schema: {e}")
            return False

    def run_setup(self) -> bool:
        """
        Run complete database setup.

        Returns:
            bool: True if all setup steps were successful
        """
        logger.info("Starting database setup...")

        # Setup schema first
        if not self.setup_database_schema():
            logger.error("Failed to setup database schema")
            return False

        # Create IAM user if IAM authentication is enabled
        iam_auth_enabled = os.getenv("ENABLE_IAM_AUTH", "false").lower() == "true"
        if iam_auth_enabled:
            if not self.create_iam_user():
                logger.error("Failed to create IAM database user")
                return False
        else:
            logger.info("IAM authentication disabled, skipping IAM user creation")

        logger.info("Database setup completed successfully")
        return True


def run_database_setup() -> bool:
    """
    Convenience function to run database setup.

    Returns:
        bool: True if setup was successful
    """
    setup = DatabaseSetup()
    return setup.run_setup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    success = run_database_setup()
    if success:
        print("✅ Database setup completed successfully")
    else:
        print("❌ Database setup failed")
        exit(1)
