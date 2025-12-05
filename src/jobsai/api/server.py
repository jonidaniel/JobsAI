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
import asyncio
import json
from io import BytesIO
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

# from pydantic import ValidationError
from fastapi import FastAPI, Response, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

import jobsai.main as backend

# Frontend payload validation
from jobsai.config.schemas import FrontendPayload
from jobsai.utils.exceptions import CancellationError

logger = logging.getLogger(__name__)

# ------------- State Management -------------
# In-memory storage for pipeline state
# In production, consider using Redis or a database for persistence
pipeline_states: Dict[str, Dict] = (
    {}
)  # {job_id: {status, progress, result, error, created_at}}
cancellation_flags: Dict[str, bool] = defaultdict(bool)  # {job_id: bool}

# Cleanup old completed jobs (older than 1 hour)
JOB_RETENTION_HOURS = 1

# ------------- FastAPI Setup -------------

# Create the FastAPI app
app = FastAPI(
    title="JobsAI Backend",
    description="API that triggers the JobsAI pipeline",
    version="1.0",
)
# Define the allowed origins for CORS
origins = [
    "http://localhost:3000",  # your frontend URL (if using a dev server)
    "http://127.0.0.1:3000",  # optional
    "*",  # allow all origins (only for development)
]

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow any origin
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods: GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # allow all headers
)


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


# ------------- Background Task -------------
def run_pipeline_async(job_id: str, payload: FrontendPayload):
    """
    Run pipeline asynchronously and update state.

    This function runs in a background thread (FastAPI BackgroundTasks handles this).
    The pipeline itself is synchronous, so this function is also synchronous.
    """
    try:
        answers = payload.model_dump(by_alias=True)

        def progress_callback(phase: str, message: str):
            """Update progress state for SSE streaming."""
            if job_id in pipeline_states:
                pipeline_states[job_id]["progress"] = {
                    "phase": phase,
                    "message": message,
                }

        def cancellation_check() -> bool:
            """Check if pipeline should be cancelled."""
            return cancellation_flags.get(job_id, False)

        # Run pipeline with progress callback and cancellation check
        # This is a blocking call, but it runs in a background thread
        result = backend.main(answers, progress_callback, cancellation_check)

        # Store result
        pipeline_states[job_id].update(
            {
                "status": "complete",
                "result": {
                    "document": result["document"],
                    "filename": result["filename"],
                    "timestamp": result["timestamp"],
                },
            }
        )

    except CancellationError:
        pipeline_states[job_id]["status"] = "cancelled"
        logger.info(f" Pipeline {job_id} was cancelled")
    except Exception as e:
        pipeline_states[job_id].update(
            {
                "status": "error",
                "error": str(e),
            }
        )
        logger.error(f" Pipeline {job_id} failed: {str(e)}")


# ------------- New API Routes -------------
@app.post("/api/start")
async def start_pipeline(
    payload: FrontendPayload, background_tasks: BackgroundTasks
) -> JSONResponse:
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
    job_id = str(uuid.uuid4())

    # Initialize state
    pipeline_states[job_id] = {
        "status": "running",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": datetime.now(),
    }

    # Run pipeline in background task
    background_tasks.add_task(run_pipeline_async, job_id, payload)

    logger.info(f" Started pipeline with job_id: {job_id}")
    return JSONResponse({"job_id": job_id})


@app.get("/api/progress/{job_id}")
async def stream_progress(job_id: str):
    """
    Stream progress updates via Server-Sent Events (SSE).

    This endpoint maintains a persistent connection and streams progress
    updates as the pipeline executes. The client should use EventSource
    to connect to this endpoint.

    Progress events are sent in the format:
        data: {"phase": "profiling", "message": "Creating your profile..."}

    Final events:
        - {"status": "complete", "filename": "..."} - Pipeline completed
        - {"status": "error", "message": "..."} - Pipeline failed
        - {"status": "cancelled"} - Pipeline was cancelled

    Args:
        job_id (str): Job identifier returned from /api/start

    Returns:
        StreamingResponse: SSE stream with progress updates
    """

    async def event_generator():
        """Generate SSE events for progress updates."""
        last_progress = None

        while True:
            # Cleanup old jobs periodically
            cleanup_old_jobs()

            state = pipeline_states.get(job_id)

            if not state:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            # Send progress update if it changed
            current_progress = state.get("progress")
            if current_progress and current_progress != last_progress:
                yield f"data: {json.dumps(current_progress)}\n\n"
                last_progress = current_progress

            # Check final status
            if state["status"] == "complete":
                result = state.get("result", {})
                yield f"data: {json.dumps({'status': 'complete', 'filename': result.get('filename', 'cover_letter.docx')})}\n\n"
                break
            elif state["status"] == "error":
                yield f"data: {json.dumps({'status': 'error', 'message': state.get('error', 'Unknown error')})}\n\n"
                break
            elif state["status"] == "cancelled":
                yield f"data: {json.dumps({'status': 'cancelled'})}\n\n"
                break

            # Poll every 500ms
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/api/cancel/{job_id}")
async def cancel_pipeline(job_id: str) -> JSONResponse:
    """
    Cancel a running pipeline.

    Sets a cancellation flag that the pipeline checks during execution.
    The pipeline will stop gracefully at the next cancellation check point.

    Args:
        job_id (str): Job identifier to cancel

    Returns:
        JSONResponse: Confirmation of cancellation request
    """
    if job_id not in pipeline_states:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    cancellation_flags[job_id] = True
    pipeline_states[job_id]["status"] = "cancelling"
    logger.info(f" Cancellation requested for job_id: {job_id}")

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

    document = result.get("document")
    filename = result.get("filename", "cover_letter.docx")

    if not document:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document not available",
        )

    # Convert document to bytes
    try:
        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)
    except Exception as e:
        logger.error(f" Failed to convert document to bytes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document for download.",
        )

    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def cleanup_old_jobs():
    """Remove completed jobs older than retention period."""
    cutoff = datetime.now() - timedelta(hours=JOB_RETENTION_HOURS)
    jobs_to_remove = [
        job_id
        for job_id, state in pipeline_states.items()
        if state.get("created_at")
        and state["created_at"] < cutoff
        and state["status"] in ("complete", "error", "cancelled")
    ]

    for job_id in jobs_to_remove:
        pipeline_states.pop(job_id, None)
        cancellation_flags.pop(job_id, None)


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
