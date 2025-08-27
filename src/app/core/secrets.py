"""
AWS Secrets Manager integration for secure credential management
"""

import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from app.core.logging import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """AWS Secrets Manager client wrapper"""
    
    def __init__(self, region_name: Optional[str] = None):
        """Initialize Secrets Manager client"""
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self._cache = {}  # Simple in-memory cache
    
    def get_secret(self, secret_arn: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager
        
        Args:
            secret_arn: ARN of the secret to retrieve
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary containing secret key-value pairs
            
        Raises:
            SecretRetrievalError: If secret cannot be retrieved
        """
        if use_cache and secret_arn in self._cache:
            logger.debug(f"Using cached secret: {secret_arn}")
            return self._cache[secret_arn]
        
        try:
            logger.info(f"Retrieving secret from AWS Secrets Manager: {secret_arn}")
            response = self.client.get_secret_value(SecretId=secret_arn)
            secret_data = json.loads(response['SecretString'])
            
            # Cache the secret
            if use_cache:
                self._cache[secret_arn] = secret_data
            
            logger.info(f"Successfully retrieved secret: {secret_arn}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DecryptionFailureException':
                logger.error(f"Failed to decrypt secret {secret_arn}: {e}")
                raise SecretRetrievalError(f"Failed to decrypt secret: {secret_arn}")
            elif error_code == 'InternalServiceErrorException':
                logger.error(f"Internal service error retrieving secret {secret_arn}: {e}")
                raise SecretRetrievalError(f"Internal service error: {secret_arn}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_arn}: {e}")
                raise SecretRetrievalError(f"Invalid parameter: {secret_arn}")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_arn}: {e}")
                raise SecretRetrievalError(f"Invalid request: {secret_arn}")
            elif error_code == 'ResourceNotFoundException':
                logger.error(f"Secret not found: {secret_arn}")
                raise SecretRetrievalError(f"Secret not found: {secret_arn}")
            else:
                logger.error(f"Unknown error retrieving secret {secret_arn}: {e}")
                raise SecretRetrievalError(f"Unknown error: {secret_arn}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret JSON for {secret_arn}: {e}")
            raise SecretRetrievalError(f"Invalid secret format: {secret_arn}")
        
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_arn}: {e}")
            raise SecretRetrievalError(f"Unexpected error: {secret_arn}")
    
    def get_database_credentials(self, secret_arn: str) -> Dict[str, str]:
        """
        Retrieve database credentials from secrets manager
        
        Returns:
            Dictionary with keys: username, password, host, port, database
        """
        secret_data = self.get_secret(secret_arn)
        
        required_keys = ['username', 'password', 'host', 'database']
        missing_keys = [key for key in required_keys if key not in secret_data]
        
        if missing_keys:
            raise SecretRetrievalError(f"Missing required database credential keys: {missing_keys}")
        
        return {
            'username': secret_data['username'],
            'password': secret_data['password'],
            'host': secret_data['host'],
            'port': secret_data.get('port', 3306),
            'database': secret_data['database']
        }
    
    def get_datadog_credentials(self, api_key_arn: str, app_key_arn: str) -> Dict[str, str]:
        """
        Retrieve Datadog credentials from secrets manager
        
        Returns:
            Dictionary with keys: api_key, app_key
        """
        api_key_secret = self.get_secret(api_key_arn)
        app_key_secret = self.get_secret(app_key_arn)
        
        if 'api_key' not in api_key_secret:
            raise SecretRetrievalError("Missing 'api_key' in Datadog API key secret")
        
        if 'app_key' not in app_key_secret:
            raise SecretRetrievalError("Missing 'app_key' in Datadog app key secret")
        
        return {
            'api_key': api_key_secret['api_key'],
            'app_key': app_key_secret['app_key']
        }
    
    def get_application_secrets(self, secret_arn: str) -> Dict[str, str]:
        """
        Retrieve application-level secrets (now auto-generated)
        
        Returns:
            Dictionary with randomly generated application secrets
        """
        secret_data = self.get_secret(secret_arn)
        
        return {
            'basic_auth_username': secret_data.get('basic_auth_username'),
            'basic_auth_password': secret_data.get('basic_auth_password'),
            'jwt_secret_key': secret_data.get('jwt_secret_key')
        }
    
    def get_api_credentials(self, secret_arn: str) -> tuple[Optional[str], Optional[str]]:
        """
        Retrieve API credentials (username and password) from Secrets Manager
        
        Args:
            secret_arn: ARN of the secret containing API credentials
            
        Returns:
            Tuple of (username, password)
        """
        try:
            secret_data = self.get_secret(secret_arn)
            username = secret_data.get('basic_auth_username')
            password = secret_data.get('basic_auth_password')
            
            if not username or not password:
                raise SecretRetrievalError("Missing API credentials in secret")
            
            logger.info("API credentials retrieved successfully from Secrets Manager")
            return username, password
            
        except SecretRetrievalError:
            logger.error(f"Failed to retrieve API credentials from {secret_arn}")
            raise
    
    def clear_cache(self):
        """Clear the secrets cache"""
        self._cache.clear()
        logger.info("Secrets cache cleared")


class SecretRetrievalError(Exception):
    """Custom exception for secret retrieval errors"""
    pass


# Global secrets manager instance - will be initialized with region when first used
secrets_manager = None


def get_secrets_manager():
    """Get or create the global secrets manager instance with proper region"""
    global secrets_manager
    if secrets_manager is None:
        from app.core.config import settings
        secrets_manager = SecretsManager(region_name=settings.aws_region)
    return secrets_manager


def get_secret_value(secret_arn: str, key: str, default: Any = None) -> Any:
    """
    Convenience function to get a specific value from a secret
    
    Args:
        secret_arn: ARN of the secret
        key: Key to retrieve from the secret
        default: Default value if key is not found
        
    Returns:
        The secret value or default
    """
    try:
        secrets_mgr = get_secrets_manager()
        secret_data = secrets_mgr.get_secret(secret_arn)
        return secret_data.get(key, default)
    except SecretRetrievalError:
        logger.warning(f"Failed to retrieve secret {secret_arn}, using default for key {key}")
        return default


def load_secrets_into_environment():
    """
    Load secrets into environment variables for backward compatibility
    This function can be called during application startup
    """
    import os
    from app.core.config import settings
    
    try:
        secrets_mgr = get_secrets_manager()
        
        # Load application secrets (API credentials, JWT secret)
        if hasattr(settings, 'api_credentials_secret_name') and settings.use_secrets_manager:
            logger.info(f"Loading application secrets from: {settings.api_credentials_secret_name}")
            
            app_secrets = secrets_mgr.get_application_secrets(settings.api_credentials_secret_name)
            
            if app_secrets['basic_auth_username']:
                os.environ['BASIC_AUTH_USERNAME'] = app_secrets['basic_auth_username']
            if app_secrets['basic_auth_password']:
                os.environ['BASIC_AUTH_PASSWORD'] = app_secrets['basic_auth_password']
            if app_secrets['jwt_secret_key']:
                os.environ['JWT_SECRET_KEY'] = app_secrets['jwt_secret_key']
            
            logger.info("Application secrets loaded from Secrets Manager")
        
        # Load database credentials if available
        if hasattr(settings, 'database_credentials_secret_arn'):
            db_creds = secrets_mgr.get_database_credentials(
                settings.database_credentials_secret_arn
            )
            os.environ['DB_HOST'] = db_creds['host']
            os.environ['DB_USER'] = db_creds['username']
            os.environ['DB_PASSWORD'] = db_creds['password']
            os.environ['DB_NAME'] = db_creds['database']
            os.environ['DB_PORT'] = str(db_creds['port'])
            
            logger.info("Database credentials loaded from Secrets Manager")
        
        # Load Datadog credentials if available
        if hasattr(settings, 'datadog_api_key_secret_arn') and hasattr(settings, 'datadog_app_key_secret_arn'):
            datadog_creds = secrets_mgr.get_datadog_credentials(
                settings.datadog_api_key_secret_arn,
                settings.datadog_app_key_secret_arn
            )
            os.environ['DATADOG_API_KEY'] = datadog_creds['api_key']
            os.environ['DATADOG_APP_KEY'] = datadog_creds['app_key']
            
            logger.info("Datadog credentials loaded from Secrets Manager")
    
    except SecretRetrievalError as e:
        logger.warning(f"Failed to load some secrets from Secrets Manager: {e}")
        logger.info("Falling back to environment variables or defaults")
    
    except Exception as e:
        logger.error(f"Unexpected error loading secrets: {e}")
        logger.info("Falling back to environment variables or defaults")
