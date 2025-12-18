"""
State Helper Functions.

Helper functions for retrieving job state with fallback mechanisms.
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from jobsai.utils.state_manager import get_job_state

# In-memory storage for pipeline state (fallback for local development)
# In Lambda, DynamoDB is used for persistent state across containers
# In-memory state only works within the same container, so it's a fallback only
pipeline_states: Dict[str, Dict] = (
    {}
)  # {job_id: {status, progress, result, error, created_at}}

# Note: Job cleanup is handled by DynamoDB TTL (auto-delete after 1 hour)
# In-memory state cleanup is not needed in Lambda (containers are ephemeral)
# Cancellation is handled via DynamoDB status updates, not in-memory flags


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
