"""
JobsAI/src/jobsai/api/server.py

FastAPI server that exposes JobsAI backend entry point as an HTTP endpoint.

To run:
    python -m uvicorn jobsai.api.server:app --reload --app-dir src
"""

import logging
from io import BytesIO

from pydantic import BaseModel, ConfigDict
from fastapi import FastAPI, Response
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
    """

    # Extract dictionary from Pydantic model
    data = payload.model_dump()

    logging.info(f"Received an API request with {len(data)} fields.")

    # Run the complete agent pipeline
    # This may take several minutes depending on:
    # - Number of job boards to scrape
    # - Deep mode (whether to fetch full job descriptions)
    # - Number of LLM calls required
    result = jobsai.main(data)
    document = result["document"]
    filename = result["filename"]

    # Convert Python-docx Document object to bytes for HTTP response
    # Document is saved to in-memory buffer (BytesIO)
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)  # Reset buffer position to beginning for reading

    # Return file as HTTP response with appropriate headers
    # Browser will automatically trigger download due to Content-Disposition header
    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# For running as standalone with 'python src/jobsai/api/server.py'
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
