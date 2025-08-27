"""
Secure credential loader that retrieves secrets from AWS Secrets Manager at runtime
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class SecureCredentialLoader:
    """
    Loads credentials securely from AWS Secrets Manager instead of environment variables
    """

    def __init__(self, region_name: str = "eu-west-1"):
        self.region_name = region_name
        self.secrets_client = None
        self._cache = {}
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Secrets Manager client with error handling"""
        try:
            self.secrets_client = boto3.client("secretsmanager", region_name=self.region_name)
            logger.info(f"Secrets Manager client initialized for region {self.region_name}")
        except NoCredentialsError:
            logger.warning("AWS credentials not found. Falling back to environment variables.")
            self.secrets_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Secrets Manager client: {e}")
            self.secrets_client = None

    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve secret from AWS Secrets Manager with caching

        Args:
            secret_name: Name or ARN of the secret
            use_cache: Whether to use cached values (default: True)

        Returns:
            Dictionary containing secret values, or None if unavailable
        """
        if not self.secrets_client:
            logger.warning(f"Secrets Manager client not available for secret: {secret_name}")
            return None

        # Check cache first
        if use_cache and secret_name in self._cache:
            logger.debug(f"Using cached secret: {secret_name}")
            return self._cache[secret_name]

        try:
            logger.debug(f"Retrieving secret from AWS: {secret_name}")
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response["SecretString"])

            # Cache the result
            if use_cache:
                self._cache[secret_name] = secret_data

            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_data

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret not found: {secret_name}")
            elif error_code == "InvalidRequestException":
                logger.error(f"Invalid request for secret: {secret_name}")
            elif error_code == "InvalidParameterException":
                logger.error(f"Invalid parameter for secret: {secret_name}")
            elif error_code == "DecryptionFailureException":
                logger.error(f"Decryption failed for secret: {secret_name}")
            else:
                logger.error(f"AWS error retrieving secret {secret_name}: {e}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret JSON for {secret_name}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None

    def get_api_credentials(
        self, fallback_user: str = "admin", fallback_pass: str = "dev_password"
    ) -> tuple[str, str]:
        """
        Get API credentials with secure fallback

        Args:
            fallback_user: Fallback username if secrets unavailable
            fallback_pass: Fallback password if secrets unavailable

        Returns:
            Tuple of (username, password)
        """
        # Try to get from Secrets Manager first
        secret_name = os.getenv("API_CREDENTIALS_SECRET_NAME", "dev-inscribe-application-secrets")
        secret_data = self.get_secret(secret_name)

        if secret_data:
            username = secret_data.get("basic_auth_username")
            password = secret_data.get("basic_auth_password")

            if username and password:
                logger.info("API credentials loaded from AWS Secrets Manager")
                return username, password
            else:
                logger.warning("API credentials incomplete in Secrets Manager")

        # Fallback to environment variables
        username = os.getenv("BASIC_AUTH_USERNAME", fallback_user)
        password = os.getenv("BASIC_AUTH_PASSWORD", fallback_pass)

        if password == fallback_pass:
            logger.warning(
                "Using default fallback password - this should be changed in production!"
            )

        logger.info("API credentials loaded from environment variables")
        return username, password

    def get_database_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get database credentials from Secrets Manager

        Returns:
            Dictionary with database connection details or None
        """
        secret_name = os.getenv("RDS_CREDENTIALS_SECRET_NAME", "dev-inscribe-rds-credentials")
        secret_data = self.get_secret(secret_name)

        if secret_data:
            required_keys = ["username", "password", "host", "database"]
            if all(key in secret_data for key in required_keys):
                logger.info("Database credentials loaded from AWS Secrets Manager")
                return {
                    "username": secret_data["username"],
                    "password": secret_data["password"],
                    "host": secret_data["host"],
                    "port": secret_data.get("port", 3306),
                    "database": secret_data["database"],
                }

        logger.warning("Database credentials not available from Secrets Manager")
        return None

    def get_datadog_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get Datadog credentials from Secrets Manager

        Returns:
            Tuple of (api_key, app_key) or (None, None)
        """
        api_secret_name = os.getenv("DATADOG_API_KEY_SECRET_NAME", "dev-inscribe-datadog-api-key")
        app_secret_name = os.getenv("DATADOG_APP_KEY_SECRET_NAME", "dev-inscribe-datadog-app-key")

        api_secret = self.get_secret(api_secret_name)
        app_secret = self.get_secret(app_secret_name)

        if api_secret and app_secret:
            api_key = api_secret.get("api_key")
            app_key = app_secret.get("app_key")

            if api_key and app_key:
                logger.info("Datadog credentials loaded from AWS Secrets Manager")
                return api_key, app_key

        # Fallback to environment variables
        api_key = os.getenv("DATADOG_API_KEY")
        app_key = os.getenv("DATADOG_APP_KEY")

        if api_key and app_key:
            logger.info("Datadog credentials loaded from environment variables")
            return api_key, app_key

        logger.warning("Datadog credentials not available")
        return None, None

    def clear_cache(self):
        """Clear the credential cache"""
        self._cache.clear()
        logger.info("Credential cache cleared")


# Global instance
credential_loader = SecureCredentialLoader()


def load_credentials_at_startup():
    """
    Load all credentials at application startup and set environment variables
    This provides backward compatibility while using secure retrieval
    """
    logger.info("Loading credentials securely at startup...")

    try:
        # Load API credentials
        username, password = credential_loader.get_api_credentials()
        os.environ["BASIC_AUTH_USERNAME"] = username
        os.environ["BASIC_AUTH_PASSWORD"] = password

        # Load database credentials
        db_creds = credential_loader.get_database_credentials()
        if db_creds:
            os.environ["DB_HOST"] = db_creds["host"]
            os.environ["DB_USER"] = db_creds["username"]
            os.environ["DB_PASSWORD"] = db_creds["password"]
            os.environ["DB_NAME"] = db_creds["database"]
            os.environ["DB_PORT"] = str(db_creds["port"])

        # Load Datadog credentials
        datadog_api_key, datadog_app_key = credential_loader.get_datadog_credentials()
        if datadog_api_key and datadog_app_key:
            os.environ["DATADOG_API_KEY"] = datadog_api_key
            os.environ["DATADOG_APP_KEY"] = datadog_app_key

        logger.info("Credentials loaded successfully")

    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        logger.info("Application will use fallback/environment variable credentials")


if __name__ == "__main__":
    # Test the credential loader
    load_credentials_at_startup()
    username, password = credential_loader.get_api_credentials()
    print(f"API Username: {username}")
    print(f"API Password: {'*' * len(password) if password else 'None'}")
