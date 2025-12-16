"""
Rate Limiting Utility for API Endpoints.

This module provides rate limiting functionality to prevent abuse and control costs.
It uses DynamoDB to track request counts per IP address with configurable time windows.

Rate limiting is implemented using a token bucket algorithm with sliding window:
- Each IP address has a limited number of requests per time window
- Requests are tracked in DynamoDB with TTL for automatic cleanup
- Exceeding the limit returns HTTP 429 (Too Many Requests)

Environment Variables:
    RATE_LIMIT_REQUESTS: Maximum requests per window (default: 5)
    RATE_LIMIT_WINDOW_SECONDS: Time window in seconds (default: 3600 = 1 hour)
    RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: "true")
    DYNAMODB_TABLE_NAME: DynamoDB table name (default: "jobsai-pipeline-states")
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)

# Rate limiting configuration (from environment variables)
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600"))
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_TABLE_NAME = os.environ.get(
    "RATE_LIMIT_TABLE_NAME",
    os.environ.get("DYNAMODB_TABLE_NAME", "jobsai-pipeline-states"),
)

# Initialize DynamoDB client (lazy initialization)
_dynamodb_client: Optional[Any] = None


def get_dynamodb_client():
    """Get or create DynamoDB client using lazy initialization.

    Returns:
        boto3.client: DynamoDB client instance, or None if boto3 is not available.
    """
    global _dynamodb_client
    if _dynamodb_client is None:
        try:
            import boto3

            _dynamodb_client = boto3.client("dynamodb")
        except ImportError:
            logger.warning("boto3 not available, rate limiting will be disabled")
            _dynamodb_client = None
    return _dynamodb_client


def get_client_ip(request) -> str:
    """Extract client IP address from FastAPI request.

    Checks common headers for real IP (X-Forwarded-For, X-Real-IP) to handle
    proxies, load balancers, and API Gateway. Falls back to direct client host.

    Args:
        request: FastAPI Request object.

    Returns:
        str: Client IP address as string.
    """
    # Check X-Forwarded-For header (used by API Gateway, CloudFront, proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip

    # Check X-Real-IP header (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client host
    if request.client:
        return request.client.host

    # Last resort: return a default identifier
    return "unknown"


def check_rate_limit(ip_address: str) -> Tuple[bool, Optional[int], Optional[int]]:
    """Check if IP address has exceeded rate limit.

    Uses DynamoDB to track request counts per IP address within a sliding time window.
    Implements token bucket algorithm: each IP gets a fixed number of requests per window.

    Args:
        ip_address: Client IP address to check.

    Returns:
        Tuple[bool, Optional[int], Optional[int]]:
            - allowed (bool): True if request is allowed, False if rate limited
            - remaining (Optional[int]): Number of requests remaining in current window
            - reset_at (Optional[int]): Unix timestamp when the rate limit resets

    Note:
        If DynamoDB is unavailable or rate limiting is disabled, returns (True, None, None).
    """
    if not RATE_LIMIT_ENABLED:
        logger.debug(
            "Rate limiting is disabled",
            extra={"extra_fields": {"ip_address": ip_address}},
        )
        return True, None, None

    dynamodb_client = get_dynamodb_client()
    if not dynamodb_client:
        logger.warning(
            "DynamoDB client not available, rate limiting disabled",
            extra={"extra_fields": {"ip_address": ip_address}},
        )
        return True, None, None

    try:
        # Create a key for this IP address
        # Use a separate item per IP to avoid hot partitions
        rate_limit_key = f"rate_limit:{ip_address}"

        # Get current time and window boundaries
        current_time = int(time.time())
        window_start = current_time - (current_time % RATE_LIMIT_WINDOW_SECONDS)
        ttl = current_time + RATE_LIMIT_WINDOW_SECONDS + 300  # 5 min buffer for cleanup
        reset_at = window_start + RATE_LIMIT_WINDOW_SECONDS

        # Use atomic increment with UpdateItem to avoid race conditions
        # This replaces the get_item + update_item pattern with a single atomic operation
        try:
            from botocore.exceptions import ClientError

            # Try to atomically increment count if window matches and count < limit
            # This prevents exceeding the limit while still being atomic
            try:
                response = dynamodb_client.update_item(
                    TableName=RATE_LIMIT_TABLE_NAME,
                    Key={"job_id": {"S": rate_limit_key}},
                    UpdateExpression="ADD #count :one SET #window = :window, #ttl = :ttl",
                    ConditionExpression="#window = :window AND #count < :limit",
                    ExpressionAttributeNames={
                        "#count": "count",
                        "#window": "window_start",
                        "#ttl": "ttl",
                    },
                    ExpressionAttributeValues={
                        ":one": {"N": "1"},
                        ":window": {"N": str(window_start)},
                        ":limit": {"N": str(RATE_LIMIT_REQUESTS)},
                        ":ttl": {"N": str(ttl)},
                    },
                    ReturnValues="ALL_NEW",
                )

                # Successfully incremented - get the new count
                new_count = int(response["Attributes"]["count"]["N"])
                remaining = max(0, RATE_LIMIT_REQUESTS - new_count)
                logger.debug(
                    "Rate limit check passed",
                    extra={
                        "extra_fields": {
                            "ip_address": ip_address,
                            "request_count": new_count,
                            "rate_limit": RATE_LIMIT_REQUESTS,
                            "remaining": remaining,
                        }
                    },
                )
                return True, remaining, reset_at

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "ConditionalCheckFailedException":
                    # Condition failed - either window doesn't match, item doesn't exist, or limit exceeded
                    # Check if it's because limit was exceeded
                    try:
                        # Try to get current state to check if limit exceeded
                        get_response = dynamodb_client.get_item(
                            TableName=RATE_LIMIT_TABLE_NAME,
                            Key={"job_id": {"S": rate_limit_key}},
                        )
                        if "Item" in get_response:
                            stored_window = int(
                                get_response["Item"]["window_start"]["N"]
                            )
                            count = int(get_response["Item"]["count"]["N"])

                            # If same window and count >= limit, rate limit exceeded
                            if (
                                stored_window == window_start
                                and count >= RATE_LIMIT_REQUESTS
                            ):
                                logger.warning(
                                    "Rate limit exceeded",
                                    extra={
                                        "extra_fields": {
                                            "ip_address": ip_address,
                                            "request_count": count,
                                            "rate_limit": RATE_LIMIT_REQUESTS,
                                            "reset_at": reset_at,
                                        }
                                    },
                                )
                                return False, 0, reset_at

                            # Window changed - reset count
                            if stored_window != window_start:
                                dynamodb_client.update_item(
                                    TableName=RATE_LIMIT_TABLE_NAME,
                                    Key={"job_id": {"S": rate_limit_key}},
                                    UpdateExpression="SET #count = :one, #window = :window, #ttl = :ttl",
                                    ExpressionAttributeNames={
                                        "#count": "count",
                                        "#window": "window_start",
                                        "#ttl": "ttl",
                                    },
                                    ExpressionAttributeValues={
                                        ":one": {"N": "1"},
                                        ":window": {"N": str(window_start)},
                                        ":ttl": {"N": str(ttl)},
                                    },
                                )
                                new_count = 1
                                remaining = RATE_LIMIT_REQUESTS - new_count
                                logger.debug(
                                    "Rate limit check passed (new window)",
                                    extra={
                                        "extra_fields": {
                                            "ip_address": ip_address,
                                            "request_count": new_count,
                                            "rate_limit": RATE_LIMIT_REQUESTS,
                                            "remaining": remaining,
                                            "window_reset": True,
                                        }
                                    },
                                )
                                return True, remaining, reset_at
                    except Exception:
                        pass  # Fall through to create new item

                    # Item doesn't exist or other error - create new one
                    dynamodb_client.put_item(
                        TableName=RATE_LIMIT_TABLE_NAME,
                        Item={
                            "job_id": {"S": rate_limit_key},
                            "count": {"N": "1"},
                            "window_start": {"N": str(window_start)},
                            "ttl": {"N": str(ttl)},
                        },
                    )

                    new_count = 1
                    remaining = RATE_LIMIT_REQUESTS - new_count
                    logger.debug(
                        "Rate limit check passed (first request)",
                        extra={
                            "extra_fields": {
                                "ip_address": ip_address,
                                "request_count": new_count,
                                "rate_limit": RATE_LIMIT_REQUESTS,
                                "remaining": remaining,
                            }
                        },
                    )
                    return True, remaining, reset_at
                else:
                    # Other error - re-raise
                    raise

        except Exception as e:
            logger.error(
                "Error checking rate limit in DynamoDB",
                extra={
                    "extra_fields": {
                        "ip_address": ip_address,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
                exc_info=True,
            )
            # On error, allow the request (fail open) but log the error
            return True, None, None

    except Exception as e:
        logger.error(
            "Unexpected error in rate limit check",
            extra={
                "extra_fields": {
                    "ip_address": ip_address,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        # On error, allow the request (fail open) but log the error
        return True, None, None
