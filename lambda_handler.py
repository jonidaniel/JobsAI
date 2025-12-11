"""
AWS Lambda handler for FastAPI application.

This handler uses Mangum to adapt the FastAPI application for AWS Lambda.
The FastAPI app is imported and wrapped with Mangum's ASGI adapter.

Lambda Configuration:
    - Handler: lambda_handler.handler
    - Runtime: Python 3.12
    - Timeout: Set appropriately for your pipeline (recommended: 15 minutes for long-running jobs)
    - Memory: Adjust based on your needs (recommended: 1024 MB minimum)
    - Environment Variables: Set OPENAI_API_KEY and other required secrets
"""

import logging
from mangum import Mangum
from jobsai.api.server import app

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
# This is the entry point that AWS Lambda calls
#
# Configuration:
#   - lifespan="off": Disables lifespan events (startup/shutdown) which Lambda doesn't support
#   - text_mime_types: Ensures proper handling of text responses including SSE streams
handler = Mangum(
    app,
    lifespan="off",
    text_mime_types=[
        "text/event-stream",  # For SSE progress streaming (/api/progress endpoint)
        "application/json",
        "text/plain",
    ],
)
