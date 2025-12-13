"""
AWS Lambda Handler for FastAPI Application and Worker Functions.

This module provides the main Lambda entry point that routes incoming requests to either:
1. FastAPI application (via Mangum) for HTTP API Gateway/Function URL requests
2. Worker handler for asynchronous pipeline execution

The handler automatically detects the request type based on the event structure:
- Events with "httpMethod" or no "job_id" → API Gateway/Function URL → FastAPI app
- Events with "job_id" and no "httpMethod" → Direct Lambda invocation → Worker handler

Lambda Configuration:
    Handler: lambda_handler.handler
    Runtime: Python 3.12
    Timeout:
        - API requests: 29 seconds (API Gateway limit)
        - Worker invocations: 15 minutes (for long-running pipelines)
    Memory: 1024 MB minimum (recommended for LLM operations)

Environment Variables:
    OPENAI_API_KEY: OpenAI API key for LLM operations
    DYNAMODB_TABLE_NAME: DynamoDB table for job state (default: "jobsai-pipeline-states")
    S3_DOCUMENTS_BUCKET: S3 bucket name for document storage
    WORKER_LAMBDA_FUNCTION_NAME: Lambda function name for async worker invocations
    FRONTEND_URL: Frontend domain for CORS configuration (optional)
"""

import logging
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
    """Main Lambda handler that routes incoming requests to appropriate handlers.

    This function serves as the entry point for all Lambda invocations. It examines
    the event structure to determine whether the request is:
    - An HTTP request from API Gateway/Function URL (routed to FastAPI)
    - A direct Lambda invocation for pipeline execution (routed to worker)

    Args:
        event: Lambda event object. Structure varies by invocation type:
            - API Gateway: Contains "httpMethod", "path", "headers", "body", etc.
            - Direct invocation: Contains "job_id" and "payload" keys
        context: Lambda context object providing runtime information.

    Returns:
        dict: Response dictionary. Format depends on handler:
            - FastAPI: Mangum-formatted response with statusCode, headers, body
            - Worker: Simple dict with statusCode and body

    Note:
        The routing logic checks for "job_id" in the event and absence of "httpMethod"
        to identify worker invocations. All other events are treated as HTTP requests.
    """
    # Check if this is a worker invocation (has job_id in event)
    if isinstance(event, dict) and "job_id" in event and "httpMethod" not in event:
        logger.info("Routing to worker handler")
        return worker_handler(event, context)

    # Otherwise, route to FastAPI app (API Gateway/Function URL)
    logger.info("Routing to API handler")
    return api_handler(event, context)
