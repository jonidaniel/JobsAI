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

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)

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
        logger.debug("Rate limiting is disabled")
        return True, None, None

    dynamodb_client = get_dynamodb_client()
    if not dynamodb_client:
        logger.warning("DynamoDB client not available, rate limiting disabled")
        return True, None, None

    try:
        # Create a key for this IP address
        # Use a separate item per IP to avoid hot partitions
        rate_limit_key = f"rate_limit:{ip_address}"

        # Get current time and window boundaries
        current_time = int(time.time())
        window_start = current_time - (current_time % RATE_LIMIT_WINDOW_SECONDS)

        # Try to get existing rate limit record
        try:
            response = dynamodb_client.get_item(
                TableName=RATE_LIMIT_TABLE_NAME,
                Key={"job_id": {"S": rate_limit_key}},
            )

            if "Item" in response:
                # Item exists, check count and window
                stored_window = int(response["Item"]["window_start"]["N"])
                count = int(response["Item"]["count"]["N"])

                # If we're in the same window, check count
                if stored_window == window_start:
                    if count >= RATE_LIMIT_REQUESTS:
                        # Rate limit exceeded
                        reset_at = stored_window + RATE_LIMIT_WINDOW_SECONDS
                        logger.warning(
                            f"Rate limit exceeded for IP {ip_address}: {count}/{RATE_LIMIT_REQUESTS} requests"
                        )
                        return False, 0, reset_at

                    # Increment count
                    new_count = count + 1
                    dynamodb_client.update_item(
                        TableName=RATE_LIMIT_TABLE_NAME,
                        Key={"job_id": {"S": rate_limit_key}},
                        UpdateExpression="SET #count = :count, #window = :window, #ttl = :ttl",
                        ExpressionAttributeNames={
                            "#count": "count",
                            "#window": "window_start",
                            "#ttl": "ttl",
                        },
                        ExpressionAttributeValues={
                            ":count": {"N": str(new_count)},
                            ":window": {"N": str(window_start)},
                            ":ttl": {
                                "N": str(current_time + RATE_LIMIT_WINDOW_SECONDS + 300)
                            },
                        },
                    )
                    remaining = RATE_LIMIT_REQUESTS - new_count
                    reset_at = window_start + RATE_LIMIT_WINDOW_SECONDS
                    logger.debug(
                        f"Rate limit check passed for IP {ip_address}: {new_count}/{RATE_LIMIT_REQUESTS} requests"
                    )
                    return True, remaining, reset_at
                else:
                    # New window, reset count
                    new_count = 1
                    dynamodb_client.update_item(
                        TableName=RATE_LIMIT_TABLE_NAME,
                        Key={"job_id": {"S": rate_limit_key}},
                        UpdateExpression="SET #count = :count, #window = :window, #ttl = :ttl",
                        ExpressionAttributeNames={
                            "#count": "count",
                            "#window": "window_start",
                            "#ttl": "ttl",
                        },
                        ExpressionAttributeValues={
                            ":count": {"N": str(new_count)},
                            ":window": {"N": str(window_start)},
                            ":ttl": {
                                "N": str(current_time + RATE_LIMIT_WINDOW_SECONDS + 300)
                            },
                        },
                    )
                    remaining = RATE_LIMIT_REQUESTS - new_count
                    reset_at = window_start + RATE_LIMIT_WINDOW_SECONDS
                    logger.debug(
                        f"Rate limit check passed for IP {ip_address}: {new_count}/{RATE_LIMIT_REQUESTS} requests (new window)"
                    )
                    return True, remaining, reset_at
            else:
                # No existing record, create new one
                new_count = 1
                ttl = (
                    current_time + RATE_LIMIT_WINDOW_SECONDS + 300
                )  # 5 min buffer for cleanup
                dynamodb_client.put_item(
                    TableName=RATE_LIMIT_TABLE_NAME,
                    Item={
                        "job_id": {"S": rate_limit_key},
                        "count": {"N": str(new_count)},
                        "window_start": {"N": str(window_start)},
                        "ttl": {"N": str(ttl)},
                    },
                )
                remaining = RATE_LIMIT_REQUESTS - new_count
                reset_at = window_start + RATE_LIMIT_WINDOW_SECONDS
                logger.debug(
                    f"Rate limit check passed for IP {ip_address}: {new_count}/{RATE_LIMIT_REQUESTS} requests (first request)"
                )
                return True, remaining, reset_at

        except Exception as e:
            logger.error(
                f"Error checking rate limit in DynamoDB: {str(e)}", exc_info=True
            )
            # On error, allow the request (fail open) but log the error
            return True, None, None

    except Exception as e:
        logger.error(f"Unexpected error in rate limit check: {str(e)}", exc_info=True)
        # On error, allow the request (fail open) but log the error
        return True, None, None
