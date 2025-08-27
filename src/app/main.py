"""
FastAPI application factory for Inscribe Customer Data Service
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
    """Legacy database manager for backward compatibility with tests"""

    @staticmethod
    def get_connection():
        """Get connection using the modular database manager"""
        return db_manager.get_connection()


def authenticate_simple(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Simple authentication for legacy endpoints"""
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
    """Application lifespan management"""
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
    """Create and configure the FastAPI application"""

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
