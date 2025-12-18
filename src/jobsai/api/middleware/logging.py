"""
Request Logging Middleware.

Logs all incoming HTTP requests with structured context for CloudWatch Logs Insights queries.
"""

import time
from typing import Any
from fastapi import Request
from jobsai.utils.logger import get_logger, set_correlation_id
from jobsai.utils.rate_limiter import get_client_ip

logger = get_logger(__name__)


async def log_requests_middleware(request: Request, call_next: Any) -> Any:
    """Log all incoming HTTP requests with structured context.

    Middleware function that logs every incoming request with structured fields
    for CloudWatch Logs Insights queries. Includes method, path, client IP,
    and response status code.

    Args:
        request: FastAPI Request object containing request details.
        call_next: Callable that processes the request and returns the response.

    Returns:
        Response: The response from the next middleware/handler.
    """
    start_time = time.time()
    client_ip = get_client_ip(request)

    # Set correlation ID from headers
    request_id = (
        request.headers.get("X-Request-ID")
        or request.headers.get("X-Amzn-Trace-Id", "").split("=")[-1]
        or None
    )
    set_correlation_id(request_id=request_id)

    logger.info(
        "HTTP request",
        extra={
            "extra_fields": {
                "http_method": request.method,
                "http_path": request.url.path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent", ""),
            }
        },
    )

    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    logger.info(
        "HTTP response",
        extra={
            "extra_fields": {
                "http_method": request.method,
                "http_path": request.url.path,
                "http_status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        },
    )

    return response
