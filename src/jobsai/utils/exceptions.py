"""
Custom exceptions for JobsAI pipeline.
"""


class CancellationError(Exception):
    """Raised when pipeline execution is cancelled by user."""

    pass
