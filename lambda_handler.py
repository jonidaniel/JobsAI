"""
AWS Lambda handler for FastAPI application and worker functions.

This handler routes requests to either:
1. FastAPI app (via Mangum) for API Gateway/Function URL requests
2. Worker handler for async pipeline execution

Lambda Configuration:
    - Handler: lambda_handler.handler
    - Runtime: Python 3.12
    - Timeout: Set appropriately (API: 29s, Worker: 15 minutes)
    - Memory: Adjust based on your needs (recommended: 1024 MB minimum)
    - Environment Variables: Set OPENAI_API_KEY, DYNAMODB_TABLE_NAME, S3_DOCUMENTS_BUCKET, WORKER_LAMBDA_FUNCTION_NAME
"""

import logging
import json
from mangum import Mangum
from jobsai.api.server import app
from lambda_worker import worker_handler

# Configure logging for Lambda
# Lambda automatically captures stdout/stderr, so we configure logging to use them
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info("Lambda handler initialized")

# Create Mangum handler to wrap FastAPI app for Lambda
# This handles API Gateway and Function URL requests
# Note: For binary content (like .docx files), API Gateway requires base64 encoding
# Mangum handles this automatically when the response content is bytes
api_handler = Mangum(
    app,
    lifespan="off",
    text_mime_types=[
        "text/event-stream",  # For SSE progress streaming (/api/progress endpoint)
        "application/json",
        "text/plain",
    ],
)


def handler(event, context):
    """
    Main Lambda handler that routes requests.

    Routes:
    - API Gateway/Function URL requests → FastAPI app (via Mangum)
    - Direct Lambda invocation with job_id → Worker handler
    """
    # Check if this is a worker invocation (has job_id in event)
    if isinstance(event, dict) and "job_id" in event and "httpMethod" not in event:
        logger.info("Routing to worker handler")
        return worker_handler(event, context)

    # Otherwise, route to FastAPI app (API Gateway/Function URL)
    logger.info("Routing to API handler")
    return api_handler(event, context)
