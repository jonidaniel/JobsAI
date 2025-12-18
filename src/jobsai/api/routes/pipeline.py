"""
Pipeline API Routes.

Routes for starting, tracking progress, and cancelling pipeline jobs.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from jobsai.config.schemas import FrontendPayload
from jobsai.utils.state_manager import store_job_state, update_job_status
from jobsai.utils.logger import get_logger, set_correlation_id, log_performance
from jobsai.api.handlers.lambda_invocation import invoke_worker_lambda
from jobsai.api.utils.state_helpers import (
    get_job_state_with_fallback,
    pipeline_states,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/start")
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
    job_id = str(uuid.uuid4())
    set_correlation_id(job_id=job_id)

    logger.info("Pipeline start requested", extra={"extra_fields": {"job_id": job_id}})

    # Initialize state in DynamoDB IMMEDIATELY
    # This ensures state exists before async invocation
    initial_state = {
        "status": "running",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": datetime.now(),
    }

    # Add delivery method and email if provided
    if payload.delivery_method:
        initial_state["delivery_method"] = payload.delivery_method
    if payload.email:
        initial_state["email"] = payload.email

    # Store in DynamoDB (primary) and in-memory (fallback for local dev)
    try:
        with log_performance("store_initial_state", job_id=job_id):
            store_job_state(job_id, initial_state)
        logger.info(
            "Stored initial state",
            extra={"extra_fields": {"job_id": job_id, "status": "running"}},
        )
    except Exception as e:
        logger.warning(
            "Failed to store state in DynamoDB",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "fallback": "in_memory",
                }
            },
        )
    # Keep in-memory copy for local development fallback
    pipeline_states[job_id] = initial_state

    # Get worker function name for logging
    import os

    worker_function_name = os.environ.get(
        "WORKER_LAMBDA_FUNCTION_NAME", os.environ.get("LAMBDA_FUNCTION_NAME")
    )

    # Invoke worker Lambda asynchronously
    # This ensures the pipeline runs in a separate Lambda invocation
    try:
        invoke_worker_lambda(job_id, payload)
        logger.info(
            "Invoked worker Lambda",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "function_name": worker_function_name,
                }
            },
        )
    except Exception as e:
        logger.error(
            "Failed to start pipeline",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        # Update state to error
        update_job_status(job_id, "error", error=f"Failed to start pipeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start pipeline",
        )

    return JSONResponse({"job_id": job_id})


@router.get("/progress/{job_id}")
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
    set_correlation_id(job_id=job_id)

    # Get state from DynamoDB with in-memory fallback
    state = get_job_state_with_fallback(job_id)

    logger.info(
        "Retrieved job state",
        extra={
            "extra_fields": {
                "job_id": job_id,
                "status": state.get("status"),
                "has_progress": bool(state.get("progress")),
                "progress": state.get("progress"),
            }
        },
    )

    # Build response based on current state
    response_data = {
        "status": state["status"],
    }

    # Add progress if available
    if state.get("progress"):
        response_data["progress"] = state["progress"]
        logger.info(
            "Including progress in response",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "progress_phase": state["progress"].get("phase"),
                    "progress_message": state["progress"].get("message"),
                }
            },
        )

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


@router.post("/cancel/{job_id}")
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

    set_correlation_id(job_id=job_id)

    # Update status in DynamoDB (worker Lambda reads from here)
    try:
        update_job_status(job_id, "cancelling")
        logger.info(
            "Cancellation requested",
            extra={"extra_fields": {"job_id": job_id, "status": "cancelling"}},
        )
    except Exception as e:
        logger.warning(
            "Failed to update cancellation in DynamoDB",
            extra={"extra_fields": {"job_id": job_id, "error": str(e)}},
        )
        # Fallback: update in-memory state for local dev
        if job_id in pipeline_states:
            pipeline_states[job_id]["status"] = "cancelling"

    return JSONResponse({"status": "cancellation_requested"})
