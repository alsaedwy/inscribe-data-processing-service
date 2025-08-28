"""
Configuration management for the Inscribe Customer Data Service.

This module provides centralized configuration management using Pydantic settings
for the Inscribe Customer Data Processing Service. It handles:

- Application settings (name, version, debug mode, environment)
- Database configuration (traditional and IAM authentication)
- Security settings (API credentials, CORS, Secrets Manager)
- Observability settings (Datadog, logging)
- Health check configuration
- Environment-specific configurations

The configuration automatically adapts based on the deployment environment
(development, staging, production) and supports both traditional database
authentication and AWS IAM database authentication.

Example:
    ```python
    from app.core.config import settings
    # Access configuration values
    print(f"App running on port: {settings.port}")
    print(f"Environment: {settings.environment}")

    # Check environment
    if settings.is_production:
        # Production-specific logic
        pass
    ```

Attributes:
    settings (Settings): Global settings instance configured from environment

Note:
    Configuration values are loaded from environment variables and .env files
    using Pydantic's BaseSettings. In production, sensitive values like
    credentials are retrieved from AWS Secrets Manager.
"""

from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings and configuration management.

    Centralized configuration class that handles all application settings
    including database connections, authentication, observability, and
    environment-specific configurations.

    Attributes:
        app_name (str): Name of the application
        version (str): Application version
        debug (bool): Debug mode flag
        environment (str): Deployment environment (development/staging/production)
        port (int): Port number for the application server

        db_host (str): Database host address
        db_port (int): Database port number
        db_name (str): Database name
        db_user (str): Database username
        db_password (Optional[str]): Database password

        use_iam_auth (bool): Whether to use AWS IAM database authentication
        iam_db_user (str): IAM database username
        aws_region (str): AWS region for services

        basic_auth_username (str): API basic auth username
        basic_auth_password (str): API basic auth password

        use_secrets_manager (bool): Whether to use AWS Secrets Manager
        api_credentials_secret_name (str): Name of the secrets manager secret

        cors_origins (List[str]): Allowed CORS origins

        datadog_api_key (Optional[str]): Datadog API key
        datadog_service_name (str): Service name for Datadog

        log_level (str): Logging level
        log_format (str): Log format (json/text)

    Example:
        ```python
        settings = Settings()

        # Check environment
        if settings.is_production:
            # Production configuration
            pass

        # Get database config
        db_config = settings.database_config
        ```

    Note:
        Settings are automatically loaded from environment variables and .env files.
        Validation is performed on critical settings to ensure application security.
    """

    # Application settings
    app_name: str = "Inscribe Customer Data Service"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    port: int = Field(default=8080, env="PORT")

    # Database settings
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(default=3306, env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: Optional[str] = Field(default=None, env="DB_PASSWORD")

    # IAM Database Authentication
    use_iam_auth: bool = Field(default=False, env="USE_IAM_AUTH")
    iam_db_user: str = Field(default="iam_app_user", env="IAM_DB_USER")
    aws_region: str = Field(default="eu-west-1", env="AWS_REGION")

    # Database connection settings
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # Authentication settings (retrieved from Secrets Manager in production)
    basic_auth_username: str = Field(default="admin", env="BASIC_AUTH_USERNAME")
    basic_auth_password: str = Field(
        default="dev_password_change_me", env="BASIC_AUTH_PASSWORD"
    )

    # Secrets Manager configuration
    api_credentials_secret_name: str = Field(
        default="dev-inscribe-application-secrets", env="API_CREDENTIALS_SECRET_NAME"
    )
    use_secrets_manager: bool = Field(default=True, env="USE_SECRETS_MANAGER")

    @field_validator("use_secrets_manager", mode="before")
    @classmethod
    def set_secrets_manager_default(cls, v, info):
        """
        Enable secrets manager by default in production environment.

        Args:
            v: The input value for use_secrets_manager
            info: Validation info containing other field data

        Returns:
            bool: True if production environment, otherwise the original value
        """
        if "environment" in info.data and info.data["environment"] == "production":
            return True
        return v

    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Observability settings
    datadog_api_key: Optional[str] = Field(default=None, env="DATADOG_API_KEY")
    datadog_app_key: Optional[str] = Field(default=None, env="DATADOG_APP_KEY")
    datadog_service_name: str = Field(
        default="inscribe-customer-service", env="DATADOG_SERVICE_NAME"
    )
    datadog_env: str = Field(default="development", env="DATADOG_ENV")

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text

    # Health check settings
    health_check_timeout: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """
        Validate that environment is one of the allowed values.

        Args:
            v (str): Environment value to validate

        Returns:
            str: Validated environment value

        Raises:
            ValueError: If environment is not in allowed list
        """
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """
        Validate that log level is one of the standard logging levels.

        Args:
            v (str): Log level value to validate

        Returns:
            str: Validated and uppercased log level

        Raises:
            ValueError: If log level is not in allowed list
        """
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        """
        Validate that log format is one of the supported formats.

        Args:
            v (str): Log format value to validate

        Returns:
            str: Validated log format

        Raises:
            ValueError: If log format is not in allowed list
        """
        allowed_formats = ["json", "text"]
        if v not in allowed_formats:
            raise ValueError(f"Log format must be one of: {allowed_formats}")
        return v

    @property
    def is_production(self) -> bool:
        """
        Check if the application is running in production environment.

        Returns:
            bool: True if environment is 'production', False otherwise
        """
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """
        Check if the application is running in development environment.

        Returns:
            bool: True if environment is 'development', False otherwise
        """
        return self.environment == "development"

    @property
    def datadog_enabled(self) -> bool:
        """
        Check if Datadog observability is enabled.

        Returns:
            bool: True if Datadog API key is configured, False otherwise
        """
        return self.datadog_api_key is not None

    @property
    def database_config(self) -> dict:
        """
        Get database configuration based on authentication method.

        Returns a database configuration dictionary that varies based on
        whether IAM authentication or traditional username/password
        authentication is being used.

        Returns:
            dict: Database configuration parameters for connection

        Note:
            For IAM authentication, the configuration includes SSL settings
            and IAM-specific parameters. For traditional authentication,
            it includes username and password directly.
        """
        base_config = {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "charset": "utf8mb4",
            "autocommit": True,
        }

        if self.use_iam_auth:
            # IAM authentication will be handled by DatabaseManager
            # when generating connections
            base_config.update(
                {"user": self.iam_db_user, "ssl_disabled": False, "connect_timeout": 60}
            )
        else:
            # Traditional username/password authentication
            base_config.update({"user": self.db_user, "password": self.db_password})

        return base_config

    def get_api_credentials(self) -> tuple[str, str]:
        """
        Get API credentials from Secrets Manager or environment variables.

        Retrieves API authentication credentials, preferring AWS Secrets Manager
        in production environments and falling back to environment variables
        in development or if Secrets Manager is unavailable.

        Returns:
            tuple[str, str]: A tuple containing (username, password)

        Note:
            In production with Secrets Manager enabled, this method attempts
            to retrieve credentials from the configured secret. If that fails,
            it falls back to environment variables with a warning logged.

        Example:
            ```python
            username, password = settings.get_api_credentials()
            ```
        """
        if self.use_secrets_manager:
            try:
                from app.core.secrets import get_secrets_manager

                secrets_manager = get_secrets_manager()
                username, password = secrets_manager.get_api_credentials(
                    self.api_credentials_secret_name
                )
                if username and password:
                    return username, password
                else:
                    # Fallback to environment variables
                    return self.basic_auth_username, self.basic_auth_password
            except Exception as e:
                # Fallback to environment variables if Secrets Manager fails
                logger = __import__("logging").getLogger(__name__)
                logger.warning(
                    f"Failed to retrieve credentials from Secrets Manager: {e}"
                )
                return self.basic_auth_username, self.basic_auth_password
        else:
            # Use environment variables directly
            return self.basic_auth_username, self.basic_auth_password

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance
settings = Settings()
