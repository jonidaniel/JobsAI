"""
Exception Handlers for FastAPI Application.

Custom exception handlers for various error types to provide user-friendly error messages.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors and return detailed error messages.

    Custom exception handler for request validation errors. Provides detailed
    information about which fields failed validation and why, making it easier
    for frontend developers to debug form submission issues.

    Args:
        request: FastAPI Request object (unused but required by handler signature).
        exc: RequestValidationError containing validation error details.

    Returns:
        JSONResponse with status 422 (Unprocessable Entity) containing:
            - detail: List of validation errors with field paths and messages
            - message: User-friendly error message
    """
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.error(
        "Validation error",
        extra={
            "extra_fields": {
                "validation_errors": error_details,
                "http_path": request.url.path if request else None,
            }
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": error_details,
            "message": "Validation error: Please check your input data",
        },
    )
