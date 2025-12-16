"""
Structured Logging Utility for CloudWatch.

This module provides structured JSON logging optimized for CloudWatch Logs Insights.
All logs are formatted as JSON with consistent fields for easy querying and filtering.

Features:
- JSON format for CloudWatch Logs Insights queries
- Correlation IDs (request_id, job_id) for request tracing
- Lambda context integration (function_name, request_id, memory_limit)
- Performance metrics (duration, timing)
- Structured context (endpoint, method, status_code, etc.)
- Log level based on environment (DEBUG in dev, INFO in prod)

Usage:
    from jobsai.utils.logger import get_logger, log_request

    logger = get_logger(__name__)
    logger.info("Message", extra={"job_id": "123", "phase": "profiling"})

    # In Lambda handler:
    @log_request
    def handler(event, context):
        ...
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

# Determine log level from environment
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL, logging.INFO)

# Global context for correlation IDs
_log_context: Dict[str, Any] = {}


class CloudWatchJSONFormatter(logging.Formatter):
    """JSON formatter for CloudWatch Logs Insights.

    Formats log records as JSON with structured fields for easy querying.
    Includes Lambda context, correlation IDs, and custom fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: LogRecord to format.

        Returns:
            JSON string with structured log data.
        """
        # Base log structure
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add Lambda context if available
        if hasattr(record, "aws_request_id"):
            log_data["aws_request_id"] = record.aws_request_id
        if hasattr(record, "function_name"):
            log_data["function_name"] = record.function_name
        if hasattr(record, "function_version"):
            log_data["function_version"] = record.function_version
        if hasattr(record, "memory_limit_mb"):
            log_data["memory_limit_mb"] = record.memory_limit_mb

        # Add correlation IDs from global context
        if "request_id" in _log_context:
            log_data["request_id"] = _log_context["request_id"]
        if "job_id" in _log_context:
            log_data["job_id"] = _log_context["job_id"]

        # Add custom fields from extra parameter
        # The extra_fields dict is passed via the 'extra' parameter in logger calls
        # Python's logging module stores it in record.__dict__
        if hasattr(record, "extra_fields"):
            if isinstance(record.extra_fields, dict):
                log_data.update(record.extra_fields)
        # Also check for any custom attributes added directly to the record
        # (e.g., by filters or via extra parameter)
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "aws_request_id",
                "function_name",
                "function_version",
                "memory_limit_mb",
                "http_method",
                "http_path",
                "http_status_code",
                "client_ip",
                "duration_ms",
                "start_time",
                "extra_fields",
            ]:
                # Add any other custom attributes
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else None
            )

        # Add performance metrics if present
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "start_time"):
            log_data["start_time"] = record.start_time

        # Add HTTP request context if present
        if hasattr(record, "http_method"):
            log_data["http_method"] = record.http_method
        if hasattr(record, "http_path"):
            log_data["http_path"] = record.http_path
        if hasattr(record, "http_status_code"):
            log_data["http_status_code"] = record.http_status_code
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip

        return json.dumps(log_data, default=str)


def configure_logging(context: Optional[Any] = None) -> None:
    """Configure logging for Lambda with JSON formatter.

    Sets up structured JSON logging optimized for CloudWatch Logs Insights.
    Integrates Lambda context if provided.

    Args:
        context: Lambda context object (optional). If provided, extracts
            function_name, request_id, and memory_limit for log context.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove existing handlers to avoid duplicate logs
    root_logger.handlers = []

    # Create console handler (Lambda captures stdout/stderr)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)

    # Set JSON formatter
    formatter = CloudWatchJSONFormatter()
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    # Add Lambda context to log records if available
    if context:
        # Inject context into log records via filter
        class LambdaContextFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                record.function_name = getattr(context, "function_name", None)
                record.function_version = getattr(context, "function_version", None)
                record.aws_request_id = getattr(context, "aws_request_id", None)
                if hasattr(context, "memory_limit_in_mb"):
                    record.memory_limit_mb = context.memory_limit_in_mb
                return True

        handler.addFilter(LambdaContextFilter())


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured logging support.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance configured for structured JSON logging.
    """
    return logging.getLogger(name)


def set_correlation_id(
    request_id: Optional[str] = None, job_id: Optional[str] = None
) -> None:
    """Set correlation IDs for request tracing.

    Correlation IDs are added to all subsequent log records to enable
    tracing requests across Lambda invocations.

    Args:
        request_id: Request ID (from API Gateway or Lambda context).
        job_id: Job ID for pipeline execution tracing.
    """
    if request_id:
        _log_context["request_id"] = request_id
    if job_id:
        _log_context["job_id"] = job_id


def clear_correlation_ids() -> None:
    """Clear correlation IDs from log context."""
    _log_context.clear()


@contextmanager
def log_performance(operation: str, **extra_fields):
    """Context manager for logging operation performance.

    Logs start, completion, and duration of an operation.

    Args:
        operation: Operation name (e.g., "pipeline_step", "llm_call").
        **extra_fields: Additional fields to include in log records.

    Yields:
        None

    Example:
        with log_performance("llm_call", model="gpt-4"):
            result = call_llm(...)
    """
    start_time = time.time()
    logger = get_logger(__name__)

    # Store extra_fields on the record for the formatter
    class ExtraFieldsFilter(logging.Filter):
        def filter(self, record):
            record.extra_fields = {
                "operation": operation,
                "start_time": start_time,
                **extra_fields,
            }
            return True

    logger.addFilter(ExtraFieldsFilter())
    logger.info(f"Starting {operation}")
    logger.removeFilter(ExtraFieldsFilter())

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000

        class ExtraFieldsFilter(logging.Filter):
            def filter(self, record):
                record.extra_fields = {
                    "operation": operation,
                    "duration_ms": round(duration_ms, 2),
                    "status": "success",
                    **extra_fields,
                }
                return True

        logger.addFilter(ExtraFieldsFilter())
        logger.info(f"Completed {operation}")
        logger.removeFilter(ExtraFieldsFilter())
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        # Capture exception string to avoid closure issues
        error_str = str(e)

        class ExtraFieldsFilter(logging.Filter):
            def filter(self, record):
                record.extra_fields = {
                    "operation": operation,
                    "duration_ms": round(duration_ms, 2),
                    "status": "error",
                    "error": error_str,
                    **extra_fields,
                }
                return True

        logger.addFilter(ExtraFieldsFilter())
        logger.error(f"Failed {operation}", exc_info=True)
        logger.removeFilter(ExtraFieldsFilter())
        raise


def log_request(func):
    """Decorator for logging HTTP requests with structured context.

    Adds request/response logging with correlation IDs, timing, and status codes.

    Args:
        func: FastAPI route handler or Lambda handler function.

    Returns:
        Decorated function with request logging.
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Extract request from FastAPI route
        request = None
        for arg in args:
            if hasattr(arg, "method") and hasattr(arg, "url"):
                request = arg
                break

        if request:
            # Set correlation ID from headers or generate
            request_id = (
                request.headers.get("X-Request-ID")
                or request.headers.get("X-Amzn-Trace-Id", "").split("=")[-1]
                or None
            )
            set_correlation_id(request_id=request_id)

            logger = get_logger(func.__module__)
            start_time = time.time()

            # Log request
            client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not client_ip:
                client_ip = request.headers.get("X-Real-IP", "")
            if not client_ip and request.client:
                client_ip = request.client.host

            # Add HTTP context to log record
            class HTTPRequestFilter(logging.Filter):
                def filter(self, record):
                    record.http_method = request.method
                    record.http_path = request.url.path
                    record.client_ip = client_ip
                    return True

            logger.addFilter(HTTPRequestFilter())
            logger.info("HTTP request")
            logger.removeFilter(HTTPRequestFilter())

            try:
                response = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Extract status code from response
                status_code = getattr(response, "status_code", 200)

                # Add HTTP response context to log record
                class HTTPResponseFilter(logging.Filter):
                    def filter(self, record):
                        record.http_method = request.method
                        record.http_path = request.url.path
                        record.http_status_code = status_code
                        record.duration_ms = round(duration_ms, 2)
                        return True

                logger.addFilter(HTTPResponseFilter())
                logger.info("HTTP response")
                logger.removeFilter(HTTPResponseFilter())

                return response
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                # Capture exception string to avoid closure issues
                error_str = str(e)

                # Add HTTP error context to log record
                class HTTPErrorFilter(logging.Filter):
                    def filter(self, record):
                        record.http_method = request.method
                        record.http_path = request.url.path
                        record.duration_ms = round(duration_ms, 2)
                        record.extra_fields = {"error": error_str}
                        return True

                logger.addFilter(HTTPErrorFilter())
                logger.error("HTTP request failed", exc_info=True)
                logger.removeFilter(HTTPErrorFilter())
                raise
        else:
            # Not a FastAPI request, call function directly
            return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # For Lambda handlers (sync functions)
        context = None
        event = None
        for arg in args:
            if hasattr(arg, "aws_request_id"):
                context = arg
            elif isinstance(arg, dict):
                event = arg

        if context:
            set_correlation_id(request_id=context.aws_request_id)
            # Extract job_id from event if present
            if event and isinstance(event, dict):
                job_id = event.get("job_id")
                if job_id:
                    set_correlation_id(job_id=job_id)

        logger = get_logger(func.__module__)
        start_time = time.time()

        # Add Lambda invocation context
        class LambdaInvocationFilter(logging.Filter):
            def filter(self, record):
                record.extra_fields = {
                    "handler": func.__name__,
                    "event_type": (
                        "worker" if (event and event.get("job_id")) else "api"
                    ),
                }
                return True

        logger.addFilter(LambdaInvocationFilter())
        logger.info("Lambda invocation")
        logger.removeFilter(LambdaInvocationFilter())

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Add Lambda completion context
            class LambdaCompletionFilter(logging.Filter):
                def filter(self, record):
                    record.extra_fields = {
                        "handler": func.__name__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success",
                    }
                    return True

            logger.addFilter(LambdaCompletionFilter())
            logger.info("Lambda invocation completed")
            logger.removeFilter(LambdaCompletionFilter())

            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # Capture exception string to avoid closure issues
            error_str = str(e)

            # Add Lambda error context
            class LambdaErrorFilter(logging.Filter):
                def filter(self, record):
                    record.extra_fields = {
                        "handler": func.__name__,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "error": error_str,
                    }
                    return True

            logger.addFilter(LambdaErrorFilter())
            logger.error("Lambda invocation failed", exc_info=True)
            logger.removeFilter(LambdaErrorFilter())
            raise

    # Return appropriate wrapper based on function type
    import inspect

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
