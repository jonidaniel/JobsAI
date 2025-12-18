"""
Rate Limiting Middleware.

Rate limiting middleware for /api/start endpoint to prevent abuse and control costs.
"""

import os
import time
from typing import Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from jobsai.utils.rate_limiter import check_rate_limit, get_client_ip
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)


async def rate_limit_middleware(request: Request, call_next: Any) -> Any:
    """Rate limiting middleware for /api/start endpoint.

    Checks rate limits for the /api/start endpoint to prevent abuse and control costs.
    Uses IP-based rate limiting with configurable limits per time window.

    Args:
        request: FastAPI Request object containing request details.
        call_next: Callable that processes the request and returns the response.

    Returns:
        Response: The response from the next middleware/handler, or HTTP 429 if rate limited.
    """
    # TEMPORARILY DISABLED FOR TESTING - bypass rate limiting
    # TODO: Re-enable rate limiting after testing
    if request.url.path == "/api/start" and request.method == "POST":
        # Bypass rate limiting - just pass through to next handler
        return await call_next(request)

    # Only apply rate limiting to /api/start endpoint (DISABLED FOR TESTING)
    # if request.url.path == "/api/start" and request.method == "POST":
    #     client_ip = get_client_ip(request)
    #     allowed, remaining, reset_at = check_rate_limit(client_ip)
    #
    #     if not allowed:
    #         logger.warning(
    #             "Rate limit exceeded",
    #             extra={
    #                 "extra_fields": {
    #                     "client_ip": client_ip,
    #                     "http_path": request.url.path,
    #                     "http_method": request.method,
    #                     "rate_limit_reset_at": reset_at,
    #                 }
    #             },
    #         )
    #         # Get origin from request for CORS headers
    #         # Since rate limit middleware runs before CORS middleware processes the response,
    #         # we need to manually add CORS headers
    #         origin = request.headers.get("origin", "")
    #         cors_headers = {}
    #
    #         # Check if origin is allowed or if we allow all origins
    #         if "*" in origins:
    #             cors_headers["Access-Control-Allow-Origin"] = "*"
    #         elif origin and origin in origins:
    #             cors_headers["Access-Control-Allow-Origin"] = origin
    #             cors_headers["Access-Control-Allow-Credentials"] = "true"
    #         elif origins:
    #             # Fallback to first allowed origin if origin header is missing
    #             cors_headers["Access-Control-Allow-Origin"] = origins[0]
    #             cors_headers["Access-Control-Allow-Credentials"] = "true"
    #
    #         # Add other CORS headers if we're allowing the request
    #         if cors_headers:
    #             cors_headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    #             cors_headers["Access-Control-Allow-Headers"] = "*"
    #
    #         # Combine CORS headers with rate limit headers
    #         response_headers = {
    #             "X-RateLimit-Limit": str(
    #                 int(os.environ.get("RATE_LIMIT_REQUESTS", "5"))
    #             ),
    #             "X-RateLimit-Remaining": "0",
    #             "X-RateLimit-Reset": str(reset_at) if reset_at else "",
    #             "Retry-After": str(reset_at - int(time.time()) if reset_at else 3600),
    #             **cors_headers,
    #         }
    #
    #         return JSONResponse(
    #             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    #             content={
    #                 "detail": "Rate limit exceeded. Please try again later.",
    #                 "error": "too_many_requests",
    #                 "reset_at": reset_at,
    #             },
    #             headers=response_headers,
    #         )
    #
    #     # Add rate limit headers to successful responses
    #     response = await call_next(request)
    #     if remaining is not None and reset_at is not None:
    #         response.headers["X-RateLimit-Limit"] = str(
    #             int(os.environ.get("RATE_LIMIT_REQUESTS", "5"))
    #         )
    #         response.headers["X-RateLimit-Remaining"] = str(remaining)
    #         response.headers["X-RateLimit-Reset"] = str(reset_at)
    #     return response

    # For all other endpoints, pass through without rate limiting
    return await call_next(request)
