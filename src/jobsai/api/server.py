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
from io import BytesIO

# from pydantic import ValidationError
from fastapi import FastAPI, Response, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import jobsai.main as backend

# Frontend payload validation
from jobsai.config.schemas import FrontendPayload

logger = logging.getLogger(__name__)

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

    logger.error("Validation error: %s", error_details)
    logger.debug("Request body: %s", await request.body())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,
            "message": "Validation error: Please check your input data",
        },
    )


# ------------- API Route -------------
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
                    {"cover-letter-num": "5"},
                    {"cover-letter-style": "Professional"}
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

    # Extract the form data from the frontend payload
    # Use by_alias=True to get kebab-case keys (e.g., "additional-info" instead of "additional_info")
    answers = payload.model_dump(by_alias=True)

    logger.info(f"Received an API request with {len(answers)} fields.")
    logger.debug(f"Form data keys: {list(answers.keys())}")
    # Debug: Print structure of first few keys
    for key, value in list(answers.items())[:3]:
        logger.debug(f"  {key}: {type(value)} - {str(value)[:200]}")

    try:
        # Run the complete JobsAI pipeline
        # This may take several minutes depending on:
        # - Number of job boards to scrape
        # - Deep mode (whether to fetch full job descriptions)
        # - Number of LLM calls required
        cover_letters = backend.main(answers)

        # Validate result structure
        if not isinstance(cover_letters, dict):
            logger.error(
                "Pipeline returned invalid result type: %s", type(cover_letters)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline returned invalid result format.",
            )

        document = cover_letters.get("document")
        filename = cover_letters.get("filename")

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
            # Convert the document to bytes and save it to a buffer
            buffer = BytesIO()
            # Save the document to the buffer
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

    # except ValidationError as e:
    #     # Handle Pydantic validation errors (e.g., skill profile validation failed)
    #     error_msg = "Invalid skill profile format."
    #     logger.error("Pydantic validation error: %s", str(e))
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=error_msg,
    #     )

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


# For running as standalone server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
