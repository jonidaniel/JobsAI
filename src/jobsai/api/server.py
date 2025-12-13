"""
FastAPI server that exposes the JobsAI backend entry point as an HTTP endpoint.

The server is responsible for receiving the form data from the frontend,
validating it, and then triggering the JobsAI pipeline.
The pipeline is responsible for generating the cover letters.
The server then returns the cover letters to the frontend.

To run the server:
    python -m uvicorn jobsai.api.server:app --reload --app-dir src
"""

import logging
import uuid
import json
import os
from typing import Dict, Optional
from datetime import datetime

# from pydantic import ValidationError
from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Frontend payload validation
from jobsai.config.schemas import FrontendPayload

from jobsai.utils.state_manager import (
    store_job_state,
    get_job_state,
    update_job_status,
)

logger = logging.getLogger(__name__)

# ------------- State Management -------------
# In-memory storage for pipeline state (fallback for local development)
# In Lambda, DynamoDB is used for persistent state across containers
# In-memory state only works within the same container, so it's a fallback only
pipeline_states: Dict[str, Dict] = (
    {}
)  # {job_id: {status, progress, result, error, created_at}}

# Note: Job cleanup is handled by DynamoDB TTL (auto-delete after 1 hour)
# In-memory state cleanup is not needed in Lambda (containers are ephemeral)
# Cancellation is handled via DynamoDB status updates, not in-memory flags

# ------------- FastAPI Setup -------------

# Create the FastAPI app
app = FastAPI(
    title="JobsAI Backend",
    description="API that triggers the JobsAI pipeline",
    version="1.0",
)
# Define the allowed origins for CORS
# Update this with your production frontend URL (S3/CloudFront domain)
# Get frontend URL from environment variable, or use defaults
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

origins = [
    "http://localhost:3000",  # local development
    "http://127.0.0.1:3000",  # local development
    "https://www.jonimakinen.com",  # production frontend
    "https://jonimakinen.com",  # production frontend (without www)
]

# Add production frontend URL from environment variable if provided
if FRONTEND_URL and FRONTEND_URL not in origins:
    origins.append(FRONTEND_URL)

# For development, allow all origins if no production URL is set
# In production, set FRONTEND_URL environment variable in Lambda
if not FRONTEND_URL:
    origins.append("*")

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow any origin
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods: GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # allow all headers
)


# Add request logging middleware to debug
@app.middleware("http")
async def log_requests(
    request: Request, call_next: Any
) -> Any:  # Response type from FastAPI
    """Log all incoming HTTP requests for debugging and monitoring.

    Middleware function that logs every incoming request method and path,
    as well as the response status code. Useful for debugging API issues
    and monitoring request patterns in CloudWatch logs.

    Args:
        request: FastAPI Request object containing request details.
        call_next: Callable that processes the request and returns the response.

    Returns:
        Response: The response from the next middleware/handler.
    """
    print(f"[MIDDLEWARE] {request.method} {request.url.path}")
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"[MIDDLEWARE] Response status: {response.status_code}")
    return response


# Exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
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

    logger.error(" Validation error: %s", error_details)
    logger.debug(" Request body: %s", await request.body())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,
            "message": "Validation error: Please check your input data",
        },
    )


# ------------- Lambda Async Invocation -------------
def invoke_worker_lambda(job_id: str, payload: FrontendPayload) -> None:
    """Invoke Lambda worker function asynchronously to run the pipeline.

    Uses AWS Lambda's asynchronous invocation (InvocationType="Event") to start
    the pipeline in a separate Lambda invocation. This ensures the pipeline can
    run for up to 15 minutes without blocking the API response.

    The worker Lambda receives the job_id and payload, executes the pipeline,
    and updates progress in DynamoDB throughout execution.

    Args:
        job_id: Unique job identifier (UUID string) for this pipeline run.
        payload: FrontendPayload object containing validated form data.

    Raises:
        RuntimeError: If boto3 is not available (should not happen in Lambda).
        Exception: If Lambda invocation fails (permissions, function not found, etc.).

    Note:
        The function name is determined by the WORKER_LAMBDA_FUNCTION_NAME environment
        variable, with fallback to LAMBDA_FUNCTION_NAME (same function, different handler).
        The invocation is asynchronous, so this function returns immediately after
        queuing the invocation request.
    """
    try:
        import boto3

        lambda_client = boto3.client("lambda")
        worker_function_name = os.environ.get(
            "WORKER_LAMBDA_FUNCTION_NAME", os.environ.get("LAMBDA_FUNCTION_NAME")
        )

        # Prepare event payload
        event_payload = {
            "job_id": job_id,
            "payload": payload.model_dump(by_alias=True),
        }

        # Invoke Lambda asynchronously (Event invocation type)
        logger.info(
            f"Invoking worker Lambda function: {worker_function_name} for job_id: {job_id}"
        )
        response = lambda_client.invoke(
            FunctionName=worker_function_name,
            InvocationType="Event",  # Async invocation
            Payload=json.dumps(event_payload),
        )

        logger.info(
            f"Worker Lambda invoked successfully for job_id: {job_id}, StatusCode: {response.get('StatusCode')}"
        )

    except ImportError:
        logger.error("boto3 not available, cannot invoke worker Lambda")
        raise RuntimeError("boto3 not available")
    except Exception as e:
        logger.error(
            f"Failed to invoke worker Lambda for job_id: {job_id}: {str(e)}",
            exc_info=True,
        )
        raise


# ------------- New API Routes -------------
@app.post("/api/start")
async def start_pipeline(payload: FrontendPayload) -> JSONResponse:
    """Start pipeline asynchronously and return job_id for progress tracking.

    Initiates the JobsAI pipeline in the background by invoking a worker Lambda
    function asynchronously. Immediately returns a job_id that the client can use
    to poll for progress updates via the /api/progress endpoint.

    The pipeline runs in a separate Lambda invocation, allowing this endpoint to
    return quickly while the long-running pipeline executes independently.

    Args:
        payload: FrontendPayload object containing validated form data:
            - General questions (job level, job boards, deep mode, etc.)
            - Technology experience levels (slider values 0-7)
            - Multiple choice selections
            - Cover letter preferences

    Returns:
        JSONResponse with job_id:
            {
                "job_id": "uuid-string"  # Use this to poll /api/progress/{job_id}
            }

    Raises:
        HTTPException 500: If worker Lambda invocation fails or state storage fails.

    Note:
        The job state is immediately stored in DynamoDB before invoking the worker
        to ensure the job_id is available for progress polling even if the worker
        hasn't started yet.
    """
    # Explicit logging to verify endpoint is being called
    print(f"[API] /api/start called")
    logger.info("[API] /api/start endpoint called")

    job_id = str(uuid.uuid4())
    print(f"[API] Generated job_id: {job_id}")

    # Initialize state in DynamoDB IMMEDIATELY
    # This ensures state exists before async invocation
    initial_state = {
        "status": "running",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": datetime.now(),
    }

    # Store in DynamoDB (primary) and in-memory (fallback for local dev)
    try:
        store_job_state(job_id, initial_state)
        logger.info(f"Stored initial state for job_id: {job_id} in DynamoDB")
    except Exception as e:
        logger.warning(
            f"Failed to store state in DynamoDB, using in-memory only: {str(e)}"
        )
    # Keep in-memory copy for local development fallback
    pipeline_states[job_id] = initial_state

    # Invoke worker Lambda asynchronously
    # This ensures the pipeline runs in a separate Lambda invocation
    try:
        invoke_worker_lambda(job_id, payload)
        logger.info(f"Invoked worker Lambda for job_id: {job_id}")
    except Exception as e:
        logger.error(f"Failed to invoke worker Lambda: {str(e)}", exc_info=True)
        # Update state to error
        update_job_status(job_id, "error", error=f"Failed to start pipeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start pipeline",
        )

    return JSONResponse({"job_id": job_id})


@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str) -> JSONResponse:
    """Get current progress for a pipeline job.

    Returns the current status and progress information for a pipeline job.
    The client should poll this endpoint periodically (recommended: every 1-2 seconds)
    to receive real-time progress updates during pipeline execution.

    The endpoint reads state from DynamoDB (primary) with fallback to in-memory
    state for local development. This ensures progress is visible across different
    Lambda containers.

    Args:
        job_id: Unique job identifier (UUID string) returned from /api/start.

    Returns:
        JSONResponse with job status and progress:
            - Running: {
                "status": "running",
                "progress": {"phase": "profiling|searching|scoring|analyzing|generating", "message": "..."}
              }
            - Complete: {
                "status": "complete",
                "filename": "20250115_143022_cover_letter.docx"
              }
            - Error: {
                "status": "error",
                "error": "Error message describing what went wrong"
              }
            - Cancelled: {
                "status": "cancelled"
              }

    Raises:
        HTTPException 404: If job_id is not found in DynamoDB or in-memory state.

    Note:
        Progress updates are written to DynamoDB by the worker Lambda during
        pipeline execution. The polling interval should balance responsiveness
        with API rate limits (typically 1-2 seconds is optimal).
    """
    # Explicit logging to verify endpoint is being called
    print(f"[API] /api/progress/{job_id} called")
    logger.info(f"[API] /api/progress/{job_id} endpoint called")

    # Get state from DynamoDB with in-memory fallback
    state = get_job_state_with_fallback(job_id)

    logger.info(f"Retrieved state for job_id: {job_id}, status: {state.get('status')}")

    # Build response based on current state
    response_data = {
        "status": state["status"],
    }

    # Add progress if available
    if state.get("progress"):
        response_data["progress"] = state["progress"]

    # Add result if complete
    if state["status"] == "complete":
        result = state.get("result", {})
        # Handle both single document (backward compatibility) and multiple documents
        if "filenames" in result and "s3_keys" in result:
            # Multiple documents
            response_data["filenames"] = result.get("filenames", [])
            response_data["s3_keys"] = result.get("s3_keys", [])
            response_data["count"] = result.get(
                "count", len(result.get("filenames", []))
            )
        else:
            # Single document (backward compatibility)
            response_data["filename"] = result.get("filename", "cover_letter.docx")

    # Add error if failed
    if state["status"] == "error":
        response_data["error"] = state.get("error", "Unknown error")

    return JSONResponse(response_data)


@app.post("/api/cancel/{job_id}")
async def cancel_pipeline(job_id: str) -> JSONResponse:
    """Cancel a running pipeline.

    Requests cancellation of a pipeline job by updating its status to "cancelling"
    in DynamoDB. The worker Lambda checks this status during execution and will
    stop gracefully at the next cancellation check point.

    Cancellation is not immediate - the pipeline will complete its current step
    before checking for cancellation. This ensures data consistency and prevents
    partial state corruption.

    Args:
        job_id: Unique job identifier (UUID string) of the job to cancel.

    Returns:
        JSONResponse with cancellation confirmation:
            {
                "status": "cancellation_requested"
            }

    Raises:
        HTTPException 404: If job_id is not found in DynamoDB or in-memory state.

    Note:
        The cancellation status is stored in DynamoDB, which the worker Lambda
        reads via get_cancellation_flag(). The pipeline checks for cancellation
        at key points: before each major step and during long-running operations.
    """
    from jobsai.utils.state_manager import update_job_status

    # Check if job exists (will raise 404 if not found)
    get_job_state_with_fallback(job_id)

    # Update status in DynamoDB (worker Lambda reads from here)
    try:
        update_job_status(job_id, "cancelling")
        logger.info(f"Cancellation requested for job_id: {job_id}")
    except Exception as e:
        logger.warning(f"Failed to update cancellation in DynamoDB: {str(e)}")
        # Fallback: update in-memory state for local dev
        if job_id in pipeline_states:
            pipeline_states[job_id]["status"] = "cancelling"

    return JSONResponse({"status": "cancellation_requested"})


@app.get("/api/download/{job_id}")
async def download_document(
    job_id: str,
    index: Optional[int] = Query(
        None, description="Document index (1-based) for multiple documents"
    ),
) -> JSONResponse:
    """Get presigned S3 URL(s) for downloading generated cover letter document(s).

    Returns presigned S3 URLs that allow the client to download documents directly
    from S3. Supports both single document (backward compatibility) and multiple
    documents. If index is provided, returns URL for that specific document.

    The presigned URLs are valid for 1 hour and include the correct Content-Type
    and Content-Disposition headers for proper browser handling.

    Args:
        job_id: Unique job identifier (UUID string) of the completed job.
        index: Optional document index (1-based) if multiple documents exist.
            If not provided and multiple documents exist, returns all URLs.

    Returns:
        JSONResponse with download information:
            Single document:
            {
                "download_url": "https://s3...presigned-url...",
                "filename": "20250115_143022_cover_letter.docx"
            }

            Multiple documents (if index not provided):
            {
                "download_urls": [
                    {"url": "https://s3...", "filename": "20250115_143022_cover_letter.docx"},
                    {"url": "https://s3...", "filename": "20250115_143022_cover_letter_2.docx"},
                    ...
                ],
                "count": 2
            }

            Multiple documents (if index provided):
            {
                "download_url": "https://s3...presigned-url...",
                "filename": "20250115_143022_cover_letter_2.docx"
            }

    Raises:
        HTTPException 404: If job_id is not found or index is out of range.
        HTTPException 400: If job status is not "complete" (documents not ready).

    Note:
        The client should use the download_url(s) to fetch documents directly
        from S3. This avoids API Gateway binary encoding issues and provides
        better download performance. URLs expire after 1 hour.
    """
    from jobsai.utils.state_manager import get_presigned_s3_url

    # Get state from DynamoDB with in-memory fallback
    state = get_job_state_with_fallback(job_id)

    if state["status"] != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document not ready. Status: {state['status']}",
        )

    result = state.get("result")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document result not available",
        )

    # Handle multiple documents
    if "filenames" in result and "s3_keys" in result:
        filenames = result.get("filenames", [])
        s3_keys = result.get("s3_keys", [])

        if index is not None:
            # Return specific document by index (1-based)
            if index < 1 or index > len(s3_keys):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document index {index} not found. Available: 1-{len(s3_keys)}",
                )
            s3_key = s3_keys[index - 1]
            filename = filenames[index - 1]
            presigned_url = get_presigned_s3_url(s3_key)
            if presigned_url:
                return JSONResponse(
                    content={
                        "download_url": presigned_url,
                        "filename": filename,
                    }
                )
        else:
            # Return all documents
            download_urls = []
            for s3_key, filename in zip(s3_keys, filenames):
                presigned_url = get_presigned_s3_url(s3_key)
                if presigned_url:
                    download_urls.append({"url": presigned_url, "filename": filename})

            if download_urls:
                return JSONResponse(
                    content={
                        "download_urls": download_urls,
                        "count": len(download_urls),
                    }
                )

    # Handle single document (backward compatibility)
    filename = result.get("filename", "cover_letter.docx")
    s3_key = result.get("s3_key")

    if s3_key:
        presigned_url = get_presigned_s3_url(s3_key)
        if presigned_url:
            logger.info(f"Returning presigned S3 URL for download: {s3_key}")
            return JSONResponse(
                content={
                    "download_url": presigned_url,
                    "filename": filename,
                }
            )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No download URLs available",
    )


# Note: Job cleanup is handled by DynamoDB TTL (auto-delete after 1 hour)
# In-memory state is ephemeral in Lambda, so cleanup is not needed


# ------------- Helper Functions -------------
def get_job_state_with_fallback(job_id: str) -> Dict[str, Any]:
    """Get job state from DynamoDB with in-memory fallback.

    Attempts to retrieve job state from DynamoDB first (persistent across containers),
    then falls back to in-memory state for local development.

    Args:
        job_id: Unique job identifier (UUID string).

    Returns:
        Dict: Job state dictionary containing status, progress, result, etc.

    Raises:
        HTTPException 404: If job not found in DynamoDB or in-memory state.
    """
    state = get_job_state(job_id)
    if not state:
        state = pipeline_states.get(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return state


# For running as standalone server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
