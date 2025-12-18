"""
FastAPI server that exposes the JobsAI backend entry point as an HTTP endpoint.

The server is responsible for receiving the form data from the frontend,
validating it, and then triggering the JobsAI pipeline.
The pipeline is responsible for generating the cover letters.
The server then returns the cover letters to the frontend.

To run the server:
    python -m uvicorn jobsai.api.server:app --reload --app-dir src
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from jobsai.api.middleware.logging import log_requests_middleware
from jobsai.api.middleware.rate_limiting import rate_limit_middleware
from jobsai.api.handlers.exceptions import validation_exception_handler
from jobsai.api.routes import pipeline, download

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

# Add request logging middleware
app.middleware("http")(log_requests_middleware)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(pipeline.router)
app.include_router(download.router)

# For running as standalone server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
