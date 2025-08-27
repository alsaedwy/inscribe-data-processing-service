"""
Enhanced logging configuration with Datadog integration
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import settings

try:
    import datadog
    from ddtrace import tracer

    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False


class DatadogFormatter(logging.Formatter):
    """Custom formatter for structured logging compatible with Datadog"""

    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.datadog_service_name,
            "environment": settings.datadog_env,
        }

        # Add trace information if available
        if DATADOG_AVAILABLE:
            span = tracer.current_span()
            if span:
                log_entry.update(
                    {
                        "dd.trace_id": str(span.trace_id),
                        "dd.span_id": str(span.span_id),
                    }
                )

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add custom attributes from extra
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ] and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development"""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Add trace information if available
        trace_info = ""
        if DATADOG_AVAILABLE:
            span = tracer.current_span()
            if span:
                trace_info = f" [trace_id={span.trace_id} span_id={span.span_id}]"

        base_message = f"{timestamp} - {record.name} - {record.levelname}{trace_info} - {record.getMessage()}"

        if record.exc_info:
            base_message += "\n" + self.formatException(record.exc_info)

        return base_message


def setup_datadog() -> None:
    """Initialize Datadog if credentials are available"""
    if not DATADOG_AVAILABLE or not settings.datadog_enabled:
        return

    try:
        # Initialize Datadog
        datadog.initialize(
            api_key=settings.datadog_api_key,
            app_key=settings.datadog_app_key,
            host_name=f"inscribe-{settings.environment}",
        )

        # Configure Datadog tracer
        tracer.configure(
            service_name=settings.datadog_service_name,
            env=settings.datadog_env,
        )

        logging.getLogger(__name__).info(
            "Datadog integration initialized",
            extra={
                "service": settings.datadog_service_name,
                "env": settings.datadog_env,
            },
        )

    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to initialize Datadog: {e}", extra={"error": str(e)}
        )


def setup_logging() -> None:
    """Setup application logging configuration"""

    # Determine log level
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # Choose formatter based on configuration
    if settings.log_format == "json":
        formatter = DatadogFormatter()
    else:
        formatter = TextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers_config = {
        "uvicorn": logging.INFO,
        "uvicorn.error": logging.INFO,
        "uvicorn.access": logging.INFO if settings.is_development else logging.WARNING,
        "fastapi": logging.INFO,
        "pymysql": logging.WARNING,  # Reduce MySQL noise
        "ddtrace": logging.WARNING,  # Reduce Datadog tracer noise
        "datadog": logging.WARNING,  # Reduce Datadog noise
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True

    # Initialize Datadog if available
    setup_datadog()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)


# Application event logging helpers
def log_request_start(
    logger: logging.Logger, method: str, path: str, client_ip: str
) -> None:
    """Log request start"""
    logger.info(
        "Request started",
        extra={
            "event_type": "request_start",
            "http_method": method,
            "http_path": path,
            "client_ip": client_ip,
        },
    )


def log_request_end(
    logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float
) -> None:
    """Log request completion"""
    logger.info(
        "Request completed",
        extra={
            "event_type": "request_end",
            "http_method": method,
            "http_path": path,
            "http_status_code": status_code,
            "duration_ms": duration_ms,
        },
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    success: bool,
    duration_ms: Optional[float] = None,
) -> None:
    """Log database operations"""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Database {operation} {'succeeded' if success else 'failed'}",
        extra={
            "event_type": "database_operation",
            "db_operation": operation,
            "db_table": table,
            "success": success,
            "duration_ms": duration_ms,
        },
    )


def log_security_event(
    logger: logging.Logger, event: str, details: Dict[str, Any]
) -> None:
    """Log security-related events"""
    logger.warning(
        f"Security event: {event}",
        extra={"event_type": "security_event", "security_event": event, **details},
    )


def log_application_startup(
    logger: logging.Logger, version: str, environment: str
) -> None:
    """Log application startup"""
    logger.info(
        "Application started",
        extra={
            "event_type": "application_startup",
            "version": version,
            "environment": environment,
            "datadog_enabled": settings.datadog_enabled,
        },
    )


def log_application_shutdown(logger: logging.Logger) -> None:
    """Log application shutdown"""
    logger.info(
        "Application shutting down", extra={"event_type": "application_shutdown"}
    )
