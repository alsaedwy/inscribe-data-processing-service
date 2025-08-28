"""
FastAPI application factory for Inscribe Customer Data Service.

This module provides the main FastAPI application factory and configuration
for the Inscribe Customer Data Processing Service. It includes:

- Application lifecycle management
- Security middleware and authentication
- Request/response logging
- Database initialization and management
- Legacy API endpoints for backward compatibility
- Health check endpoints
- CORS configuration
- Error handling and security headers

The application supports both modern API endpoints (under /api/v1/) and
legacy endpoints for backward compatibility with existing tests and clients.

Example:
    To run the application:

    ```python
    from app.main import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
    ```

Attributes:
    app (FastAPI): The configured FastAPI application instance
    logger (Logger): Application logger instance
    security (HTTPBasic): HTTP Basic authentication handler

Note:
    The application automatically configures itself based on the environment
    (development/production) and loads secure credentials from AWS Secrets Manager
    in production environments.
"""

import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api import api_router
from app.core.config import settings
from app.core.db_setup import run_database_setup
from app.core.logging import (
    get_logger,
    log_application_shutdown,
    log_application_startup,
    log_request_end,
    log_request_start,
    setup_logging,
)
from app.core.secure_credentials import load_credentials_at_startup
from app.database.manager import DatabaseManager as ModularDatabaseManager
from app.database.manager import db_manager
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate

# Import Datadog if available
try:
    from ddtrace.contrib.fastapi import patch

    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Basic HTTP Security for simple tests
security = HTTPBasic()


# Legacy DatabaseManager for backwards compatibility
class DatabaseManager:
    """
    Legacy database manager for backward compatibility with tests.

    This class provides a compatibility layer for existing tests and code
    that expects the old DatabaseManager interface. It delegates to the
    new modular database manager internally.

    Attributes:
        None

    Note:
        This class is deprecated and maintained only for backward compatibility.
        New code should use app.database.manager.db_manager directly.
    """

    @staticmethod
    def get_connection():
        """
        Get database connection using the modular database manager.

        Returns:
            pymysql.Connection: Active database connection

        Raises:
            DatabaseConnectionError: If connection cannot be established
        """
        return db_manager.get_connection()


def authenticate_simple(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Simple HTTP Basic authentication for legacy endpoints.

    Validates user credentials against configured API credentials using
    timing-safe comparison to prevent timing attacks.

    Args:
        credentials (HTTPBasicCredentials): HTTP Basic auth credentials
            from the Authorization header

    Returns:
        str: The authenticated username

    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid

    Example:
        ```python
        @app.get("/protected")
        async def protected_endpoint(username: str = Depends(authenticate_simple)):
            return {"message": f"Hello {username}"}
        ```

    Note:
        Uses secrets.compare_digest() for timing-safe string comparison
        to prevent timing-based attacks on authentication.
    """
    expected_username, expected_password = settings.get_api_credentials()

    correct_username = secrets.compare_digest(credentials.username, expected_username)
    correct_password = secrets.compare_digest(credentials.password, expected_password)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage FastAPI application lifespan events.

    Handles application startup and shutdown procedures including:
    - Credential loading from AWS Secrets Manager
    - Database schema setup and initialization
    - Connection pool management
    - Graceful shutdown procedures

    Args:
        app (FastAPI): The FastAPI application instance

    Yields:
        None: Control is yielded back to FastAPI during normal operation

    Raises:
        Exception: Critical startup failures that prevent application start

    Note:
        Non-critical failures (like credential loading) are logged as warnings
        but don't prevent application startup to maintain availability.
    """
    # Startup
    log_application_startup(logger, settings.version, settings.environment)

    # Load credentials securely at startup
    try:
        load_credentials_at_startup()
        logger.info("Secure credentials loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load some credentials: {e}")

    # Run database setup (create IAM user, schema, etc.)
    try:
        if run_database_setup():
            logger.info("Database setup completed successfully")
        else:
            logger.warning("Database setup had some issues, but continuing...")
    except Exception as e:
        logger.warning(
            f"Database setup failed: {e}, continuing with standard initialization..."
        )

    # Initialize database
    try:
        await ModularDatabaseManager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    yield

    # Shutdown
    log_application_shutdown(logger)
    await ModularDatabaseManager.close()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    Factory function that creates a fully configured FastAPI application
    with all necessary middleware, routes, and security configurations.

    Returns:
        FastAPI: Configured application instance ready for deployment

    Features:
        - CORS middleware configuration
        - Request/response logging middleware
        - Security headers middleware
        - API route registration
        - Legacy endpoint compatibility
        - Health check endpoints
        - Error handling
        - Optional Datadog tracing integration

    Example:
        ```python
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8080)
        ```

    Note:
        The application is configured differently for development and production
        environments. Documentation endpoints are disabled in production.
    """

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Customer data processing service for Inscribe",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Log request start
        client_ip = request.client.host if request.client else "unknown"
        log_request_start(logger, request.method, str(request.url.path), client_ip)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled exceptions
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Unhandled exception in request: {e}",
                extra={
                    "event_type": "request_error",
                    "http_method": request.method,
                    "http_path": str(request.url.path),
                    "duration_ms": duration_ms,
                    "error": str(e),
                },
            )
            return JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )

        # Log request completion
        duration_ms = (time.time() - start_time) * 1000
        log_request_end(
            logger,
            request.method,
            str(request.url.path),
            response.status_code,
            duration_ms,
        )

        return response

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    # Include API routes
    app.include_router(api_router)

    # Add legacy endpoints for backward compatibility with tests
    @app.get("/health")
    async def legacy_health_check():
        """Legacy health check endpoint for backward compatibility"""
        try:
            # Test database connectivity
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            return {
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy",
            )

    @app.post("/customers", response_model=CustomerResponse)
    async def legacy_create_customer(
        customer: CustomerCreate, username: str = Depends(authenticate_simple)
    ):
        """Legacy create customer endpoint"""
        try:
            insert_sql = """
            INSERT INTO customers (first_name, last_name, email, phone, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    insert_sql,
                    (
                        customer.first_name,
                        customer.last_name,
                        customer.email,
                        customer.phone,
                        customer.address,
                        customer.date_of_birth,
                    ),
                )

                customer_id = cursor.lastrowid

                # Fetch the created customer
                select_sql = "SELECT * FROM customers WHERE id = %s"
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()

                return result
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/customers", response_model=List[CustomerResponse])
    async def legacy_get_customers(username: str = Depends(authenticate_simple)):
        """Legacy get customers endpoint"""
        try:
            select_sql = "SELECT * FROM customers ORDER BY created_at DESC"

            with db_manager.get_cursor() as cursor:
                cursor.execute(select_sql)
                results = cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"Error retrieving customers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.get("/customers/{customer_id}", response_model=CustomerResponse)
    async def legacy_get_customer(
        customer_id: int, username: str = Depends(authenticate_simple)
    ):
        """Legacy get customer endpoint"""
        try:
            select_sql = "SELECT * FROM customers WHERE id = %s"

            with db_manager.get_cursor() as cursor:
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()

                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Customer not found",
                    )
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving customer {customer_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.put("/customers/{customer_id}", response_model=CustomerResponse)
    async def legacy_update_customer(
        customer_id: int,
        customer_update: CustomerUpdate,
        username: str = Depends(authenticate_simple),
    ):
        """Legacy update customer endpoint"""
        try:
            # Build dynamic update query
            update_fields = []
            update_values = []

            update_mapping = {
                "first_name": customer_update.first_name,
                "last_name": customer_update.last_name,
                "email": customer_update.email,
                "phone": customer_update.phone,
                "address": customer_update.address,
                "date_of_birth": customer_update.date_of_birth,
            }

            for field, value in update_mapping.items():
                if value is not None:
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update",
                )

            update_sql = f"""
            UPDATE customers
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            update_values.append(customer_id)

            with db_manager.get_cursor() as cursor:
                cursor.execute(update_sql, update_values)

                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Customer not found",
                    )

                # Fetch updated customer
                select_sql = "SELECT * FROM customers WHERE id = %s"
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.delete("/customers/{customer_id}")
    async def legacy_delete_customer(
        customer_id: int, username: str = Depends(authenticate_simple)
    ):
        """Legacy delete customer endpoint"""
        try:
            delete_sql = "DELETE FROM customers WHERE id = %s"

            with db_manager.get_cursor() as cursor:
                cursor.execute(delete_sql, (customer_id,))

                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Customer not found",
                    )

                return {"message": "Customer deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # Add a simple root health check (in addition to /api/v1/health)
    @app.get("/api/health")
    async def api_health_check():
        """Simple API health check endpoint"""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.version,
        }

    # Configure Datadog tracing if available
    if DATADOG_AVAILABLE and settings.datadog_enabled:
        try:
            patch(app)
            logger.info("Datadog FastAPI tracing enabled")
        except Exception as e:
            logger.error(f"Failed to enable Datadog tracing: {e}")

    return app


# Create the app instance
app = create_app()
