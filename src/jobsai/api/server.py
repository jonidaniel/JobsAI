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
    """Run the agent pipeline.

    HandleThe request body is the JSON collected from slider and text field questions.
    """

    data = payload.model_dump()

    logging.info(f"Received an API request with {len(data)} fields.")

    # Initiate agent pipeline with the frontend payload
    result = jobsai.main(data)
    document = result["document"]
    filename = result["filename"]

    # Convert Document to BytesIO
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    # Return file as response
    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# For running as standalone with 'python src/jobsai/api/server.py'
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
