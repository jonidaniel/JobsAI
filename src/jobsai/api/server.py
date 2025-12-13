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
from io import BytesIO
from typing import Dict, Optional
from datetime import datetime

# from pydantic import ValidationError
from fastapi import FastAPI, Response, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import jobsai.main as backend

# Frontend payload validation
from jobsai.config.schemas import FrontendPayload
from jobsai.utils.exceptions import CancellationError
from jobsai.utils.state_manager import (
    store_job_state,
    get_job_state,
    update_job_progress,
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
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    print(f"[MIDDLEWARE] {request.method} {request.url.path}")
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"[MIDDLEWARE] Response status: {response.status_code}")
    return response


# Exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and return detailed error messages."""
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
    """
    Invoke Lambda worker function asynchronously to run the pipeline.

    This uses Lambda's async invocation to ensure the pipeline runs
    in a separate Lambda invocation that won't be frozen.

    Args:
        job_id: Job identifier
        payload: Frontend payload data
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
    """
    Start pipeline asynchronously and return job_id for progress tracking.

    This endpoint initiates the pipeline in the background and immediately
    returns a job_id that can be used to track progress via SSE.

    Args:
        payload (FrontendPayload): Form data from frontend

    Returns:
        JSONResponse: Contains job_id for progress tracking
            {"job_id": "uuid-string"}
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
    """
    Get current progress for a pipeline job.

    This endpoint returns the current status and progress of a pipeline job.
    The client should poll this endpoint periodically (e.g., every 1-2 seconds)
    to get progress updates.

    Response format:
        - {"status": "running", "progress": {"phase": "...", "message": "..."}}
        - {"status": "complete", "filename": "..."}
        - {"status": "error", "error": "..."}
        - {"status": "cancelled"}

    Args:
        job_id (str): Job identifier returned from /api/start

    Returns:
        JSONResponse: Current job status and progress
    """
    # Explicit logging to verify endpoint is being called
    print(f"[API] /api/progress/{job_id} called")
    logger.info(f"[API] /api/progress/{job_id} endpoint called")

    # Try to get state from DynamoDB first (persistent across containers)
    state = get_job_state(job_id)

    # Fallback to in-memory state if DynamoDB fails
    if not state:
        logger.info(
            f"State not found in DynamoDB for job_id: {job_id}, checking in-memory"
        )
        state = pipeline_states.get(job_id)

    if not state:
        logger.warning(
            f"Job {job_id} not found in DynamoDB or in-memory state. Available in-memory jobs: {list(pipeline_states.keys())}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

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
        response_data["filename"] = result.get("filename", "cover_letter.docx")

    # Add error if failed
    if state["status"] == "error":
        response_data["error"] = state.get("error", "Unknown error")

    return JSONResponse(response_data)


@app.post("/api/cancel/{job_id}")
async def cancel_pipeline(job_id: str) -> JSONResponse:
    """
    Cancel a running pipeline.

    Sets a cancellation flag in DynamoDB that the worker Lambda checks during execution.
    The pipeline will stop gracefully at the next cancellation check point.

    Args:
        job_id (str): Job identifier to cancel

    Returns:
        JSONResponse: Confirmation of cancellation request
    """
    from jobsai.utils.state_manager import get_job_state, update_job_status

    # Check if job exists in DynamoDB
    state = get_job_state(job_id)
    if not state:
        # Fallback to in-memory check
        if job_id not in pipeline_states:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

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
async def download_document(job_id: str) -> Response:
    """
    Download the generated cover letter document.

    Args:
        job_id (str): Job identifier

    Returns:
        Response: Word document (.docx) file download

    Raises:
        HTTPException: 404 if job not found or not complete
    """
    from jobsai.utils.state_manager import get_job_state, get_document_from_s3

    # Try to get state from DynamoDB first
    state = get_job_state(job_id)

    # Fallback to in-memory state
    if not state:
        state = pipeline_states.get(job_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

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

    filename = result.get("filename", "cover_letter.docx")
    s3_key = result.get("s3_key")

    # Try to get document from S3 first
    if s3_key:
        buffer = get_document_from_s3(s3_key)
        if buffer:
            return Response(
                content=buffer.read(),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    # Fallback: try in-memory document (for backward compatibility)
    document = result.get("document")
    if document:
        try:
            buffer = BytesIO()
            document.save(buffer)
            buffer.seek(0)
            return Response(
                content=buffer.read(),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logger.error(f"Failed to convert in-memory document to bytes: {str(e)}")

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Document not available in S3 or memory",
    )


# Note: Job cleanup is handled by DynamoDB TTL (auto-delete after 1 hour)
# In-memory state is ephemeral in Lambda, so cleanup is not needed


# ------------- Legacy API Route (kept for backward compatibility) -------------
# Define the API endpoint
@app.post("/api/endpoint")
async def run_pipeline(payload: FrontendPayload) -> Response:
    """
    Run the complete JobsAI backend pipeline and return cover letter document.

    This endpoint receives form data from the frontend (slider values, text fields,
    multiple choice selections) and triggers the full pipeline:
    1. ProfilerAgent: Profile creation
    2. SearcherService: Job searching
    3. ScorerService: Job scoring
    4. ReporterAgent: Report generation
    5. GeneratorAgent: Cover letter generation

    The response is a Word document (.docx) that the browser will download.

    Args:
        payload (FrontendPayload): Form data from frontend, grouped by question set.

        Structure:
            {
                "general": [
                    {"job-level": ["Expert", "Intermediate"]},
                    {"job-boards": ["Duunitori", "Jobly"]},
                    {"deep-mode": "Yes"},
                    {"cover-letter-num": 5},  # Integer (1-10)
                    {"cover-letter-style": ["Professional"]}  # Array of 1-2 strings
                ],
                "languages": [
                    {"javascript": 5},
                    {"python": 3},
                    {"text-field1": "Additional languages..."}
                ],
                "databases": [...],
                "cloud-development": [...],
                "web-frameworks": [...],
                "dev-ides": [...],
                "llms": [...],
                "doc-and-collab": [...],
                "operating-systems": [...]
                ...
            }

        Where:
            - "general": Array of single-key objects with configuration values
            - Technology sets (languages, databases, etc.): Array of single-key objects
              where keys are technology names (slider values 0-7) or "text-field{N}" (strings)
            - "additional-info": Array of single-key objects with additional information
    Returns:
        Response: HTTP response with:
            - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
            - Content-Disposition: attachment header for file download
            - Body: Binary content of the .docx file

    Raises:
        HTTPException: With appropriate status code and error message if pipeline fails
    """

    # Convert Pydantic model to dictionary for pipeline processing
    # Use by_alias=True to preserve kebab-case keys from frontend
    # (e.g., "additional-info" instead of "additional_info")
    answers = payload.model_dump(by_alias=True)

    logger.info(f" Received API request with {len(answers)} form fields")
    logger.debug(f" Form data keys: {list(answers.keys())}")
    # Log structure of first few fields for debugging
    for key, value in list(answers.items())[:3]:
        logger.debug(f" {key}: {type(value).__name__} - {str(value)[:200]}")

    try:
        # Execute the complete JobsAI pipeline
        # Pipeline execution time varies based on:
        # - Number of job boards selected (more boards = longer search time)
        # - Deep mode setting (fetching full descriptions is slower)
        # - Number of LLM calls required (profile, keywords, analysis, generation)
        # Typical execution: 2-5 minutes for a complete run
        cover_letters = backend.main(answers)

        # Validate pipeline result structure
        if not isinstance(cover_letters, dict):
            logger.error(
                " Pipeline returned invalid result type: %s", type(cover_letters)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline returned invalid result format.",
            )

        # Extract document and filename from pipeline result
        document = cover_letters.get("document")
        filename = cover_letters.get("filename")

        # Validate that pipeline returned required fields
        if document is None:
            logger.error(" Pipeline did not return a document")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate cover letter document.",
            )

        if not filename:
            logger.error(" Pipeline did not return a filename")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate document filename.",
            )

        # Convert python-docx Document object to bytes for HTTP response
        # The document is written to an in-memory buffer (BytesIO) to avoid
        # temporary file creation
        try:
            buffer = BytesIO()
            # Write document to buffer
            document.save(buffer)
            # Reset buffer position to beginning for reading
            buffer.seek(0)
        except Exception as e:
            logger.error(" Failed to convert document to bytes: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document for download.",
            )

        # Return document as HTTP response with appropriate headers
        # Content-Disposition header triggers browser download dialog
        return Response(
            content=buffer.read(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise

    except ValueError as e:
        # Handle validation errors from profiler (e.g., LLM didn't return parseable JSON)
        error_msg = str(e)
        logger.error(" Validation error in pipeline: %s", error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data or LLM response: {error_msg}",
        )

    except KeyError as e:
        # Handle missing keys in result dictionary
        error_msg = f"Pipeline result missing required field: {str(e)}"
        logger.error(" KeyError in pipeline result: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline returned incomplete results.",
        )

    except AttributeError as e:
        # Handle attribute access errors
        error_msg = "Pipeline encountered an internal error."
        logger.error(" AttributeError in pipeline: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    except FileNotFoundError as e:
        # Handle missing file errors (e.g., config files, templates)
        error_msg = "Required file not found. Please check server configuration."
        logger.error(" FileNotFoundError: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    except PermissionError as e:
        # Handle file permission errors
        error_msg = "File permission error. Please check server configuration."
        logger.error(" PermissionError: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    except Exception as e:
        # Check if this is an OpenAI-related error
        error_type = type(e).__name__
        error_module = type(e).__module__

        # Handle OpenAI API errors (connection, timeout, rate limits, etc.)
        if "openai" in error_module.lower() or "OpenAI" in error_type:
            # Check for connection/timeout errors
            if "connection" in error_type.lower() or "timeout" in error_type.lower():
                error_msg = "Unable to connect to AI service. Please try again later."
                logger.error(" OpenAI API connection/timeout error: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg,
                )
            else:
                # Other OpenAI errors (rate limits, authentication, API errors, etc.)
                error_msg = "AI service error occurred. Please try again later."
                logger.error(" OpenAI API error: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_msg,
                )

        # Catch-all for any other unexpected errors
        error_msg = "An unexpected error occurred while processing your request."
        logger.exception(" Unexpected error in pipeline: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


# For running as standalone server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
