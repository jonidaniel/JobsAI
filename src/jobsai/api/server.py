"""
JobsAI/src/jobsai/api/server.py

FastAPI server that exposes JobsAI backend entry point as an HTTP endpoint.

To run:
    python -m uvicorn jobsai.api.server:app --reload --app-dir src
"""

import logging
from typing import Dict, Any

from pydantic import BaseModel, ConfigDict
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# ------------- FastAPI Setup -------------

app = FastAPI(
    title="JobsAI Backend",
    description="API that triggers full JobsAI pipeline.",
    version="1.0",
)


class FrontendPayload(BaseModel):
    """
    Accept arbitrary key-value pairs from the frontend.
    """

    model_config = ConfigDict(extra="allow")  # Allow dynamic keys


# ------------- Pipeline Function -------------


def run(frontend_answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggers the complete JobsAI pipeline using the existing agent architecture.
    Returns a summary dictionary of what was generated.
    """

    return {
        "status": "completed",
    }


# ------------- API Route -------------
@app.post("/api/endpoint")
# async def trigger_pipeline(payload: Dict[str, Any]):
async def trigger_pipeline(payload: FrontendPayload):
    """
    Endpoint called from the frontend.
    The request body is the JSON collected from sliders & text fields.
    """

    # print(payload)
    data = payload.model_dump()

    logging.info(f"Received API request with {len(data)} fields.")

    result = run(data)
    return result


# ------------- Run Standalone -------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
