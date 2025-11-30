"""
JobsAI/src/jobsai/api/server.py

FastAPI server that exposes JobsAI backend entry point as an HTTP endpoint.

To run:
    python -m uvicorn jobsai.api.server:app --reload --app-dir src
"""

import logging
from io import BytesIO

from pydantic import BaseModel, ConfigDict, ValidationError
from fastapi import FastAPI, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import jobsai.main as jobsai

logger = logging.getLogger(__name__)

# ------------- FastAPI Setup -------------

app = FastAPI(
    title="JobsAI Backend",
    description="API that triggers full JobsAI pipeline.",
    version="1.0",
)

origins = [
    "http://localhost:3000",  # your frontend URL (if using a dev server)
    "http://127.0.0.1:3000",  # optional
    "*",  # allow all origins (only for development)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow any origin
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # allow all headers
)


class FrontendPayload(BaseModel):
    """Accept arbitrary key-value pairs from the frontend."""

    model_config = ConfigDict(extra="allow")  # Allow dynamic keys


# ------------- API Route -------------
@app.post("/api/endpoint")
async def run_agent_pipeline(payload: FrontendPayload):
    """
    Run the complete JobsAI agent pipeline and return cover letter document.

    This endpoint receives form data from the frontend (slider values, text fields,
    multiple choice selections) and triggers the full agent pipeline:
    1. Profile creation
    2. Job searching
    3. Job scoring
    4. Report generation
    5. Cover letter generation

    The response is a Word document (.docx) that the browser will download.

    Args:
        payload (FrontendPayload): Form data from frontend containing:
            - General questions (text fields)
            - Technology experience levels (slider values 0-7)
            - Multiple choice selections

    Returns:
        Response: HTTP response with:
            - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
            - Content-Disposition: attachment header for file download
            - Body: Binary content of the .docx file

    Raises:
        HTTPException: With appropriate status code and error message if pipeline fails
    """

    # Extract dictionary from Pydantic model
    form_data = payload.model_dump()

    logger.info(f"Received an API request with {len(form_data)} fields.")

    try:
        # Run the complete agent pipeline
        # This may take several minutes depending on:
        # - Number of job boards to scrape
        # - Deep mode (whether to fetch full job descriptions)
        # - Number of LLM calls required
        pipeline_result = jobsai.main(form_data)

        # Validate result structure
        if not isinstance(pipeline_result, dict):
            logger.error(
                "Pipeline returned invalid result type: %s", type(pipeline_result)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline returned invalid result format.",
            )

        document = pipeline_result.get("document")
        filename = pipeline_result.get("filename")

        if document is None:
            logger.error("Pipeline did not return a document.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate cover letter document.",
            )

        if not filename:
            logger.error("Pipeline did not return a filename.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate document filename.",
            )

        # Convert Python-docx Document object to bytes for HTTP response
        # Document is saved to in-memory buffer (BytesIO)
        try:
            buffer = BytesIO()
            document.save(buffer)
            buffer.seek(0)  # Reset buffer position to beginning for reading
        except Exception as e:
            logger.error("Failed to save document to buffer: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document for download.",
            )

        # Return file as HTTP response with appropriate headers
        # Browser will automatically trigger download due to Content-Disposition header
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
        logger.error("Validation error in pipeline: %s", error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data or LLM response: {error_msg}",
        )

    except ValidationError as e:
        # Handle Pydantic validation errors (e.g., skill profile validation failed)
        error_msg = "Invalid skill profile format."
        logger.error("Pydantic validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    except KeyError as e:
        # Handle missing keys in result dictionary
        error_msg = f"Pipeline result missing required field: {str(e)}"
        logger.error("KeyError in pipeline result: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline returned incomplete results.",
        )

    except AttributeError as e:
        # Handle attribute access errors
        error_msg = "Pipeline encountered an internal error."
        logger.error("AttributeError in pipeline: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    except FileNotFoundError as e:
        # Handle missing file errors (e.g., config files, templates)
        error_msg = "Required file not found. Please check server configuration."
        logger.error("FileNotFoundError: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    except PermissionError as e:
        # Handle file permission errors
        error_msg = "File permission error. Please check server configuration."
        logger.error("PermissionError: %s", str(e))
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
                logger.error("OpenAI API connection/timeout error: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg,
                )
            else:
                # Other OpenAI errors (rate limits, authentication, API errors, etc.)
                error_msg = "AI service error occurred. Please try again later."
                logger.error("OpenAI API error: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_msg,
                )

        # Catch-all for any other unexpected errors
        error_msg = "An unexpected error occurred while processing your request."
        logger.exception("Unexpected error in pipeline: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


# For running as standalone with 'python src/jobsai/api/server.py'
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
