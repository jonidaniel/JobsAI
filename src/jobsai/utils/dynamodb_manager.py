"""
DynamoDB Manager for Pipeline Job State.

This module handles all DynamoDB operations for storing and retrieving pipeline job state.
It provides functions for job state persistence, progress updates, and cancellation checks.

Environment Variables:
    DYNAMODB_TABLE_NAME: Name of the DynamoDB table (default: "jobsai-pipeline-states")

Note:
    All functions use lazy initialization for AWS clients to avoid import-time
    dependencies and support local development without AWS credentials.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB table name (set via environment variable or use default)
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "jobsai-pipeline-states")

# Initialize DynamoDB client (lazy initialization)
_dynamodb_client: Optional[Any] = None
_dynamodb_resource: Optional[Any] = None


def get_dynamodb_client() -> Optional[Any]:
    """Get or create DynamoDB client using lazy initialization.

    Returns:
        boto3.client: DynamoDB client instance, or None if boto3 is not available.

    Note:
        Uses global variable to cache the client instance across function calls.
        This avoids creating multiple clients and improves performance.
    """
    global _dynamodb_client
    if _dynamodb_client is None:
        try:
            import boto3

            _dynamodb_client = boto3.client("dynamodb")
        except ImportError:
            logger.warning(
                "boto3 not available",
                extra={"extra_fields": {"operation": "dynamodb_client_init"}},
            )
            _dynamodb_client = None
    return _dynamodb_client


def get_dynamodb_resource() -> Optional[Any]:
    """Get or create DynamoDB resource using lazy initialization.

    Returns:
        boto3.resource: DynamoDB resource instance, or None if boto3 is not available.

    Note:
        Uses global variable to cache the resource instance across function calls.
        The resource interface is preferred for simpler table operations.
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        try:
            import boto3

            _dynamodb_resource = boto3.resource("dynamodb")
        except ImportError:
            logger.warning(
                "boto3 not available",
                extra={"extra_fields": {"operation": "dynamodb_resource_init"}},
            )
            _dynamodb_resource = None
    return _dynamodb_resource


def store_job_state(job_id: str, state: Dict) -> None:
    """Store job state in DynamoDB.

    Creates or updates a job state record in DynamoDB with the provided state information.
    Automatically sets TTL (Time To Live) to 1 hour from creation time for automatic cleanup.

    Args:
        job_id: Unique job identifier (UUID string).
        state: State dictionary containing:
            - status (str): Current job status (e.g., "running", "complete", "error")
            - progress (dict, optional): Progress information with "phase" and "message"
            - result (dict, optional): Result data (document metadata, not the document itself)
            - error (str, optional): Error message if job failed
            - created_at (datetime): Timestamp when job was created

    Raises:
        Exception: If DynamoDB operation fails or boto3 is not available.

    Note:
        Document objects cannot be stored in DynamoDB. They must be stored separately
        in S3 using store_document_in_s3() from s3_manager module.
    """
    try:
        dynamodb = get_dynamodb_resource()
        if dynamodb is None:
            logger.error("DynamoDB resource not available")
            return

        table = dynamodb.Table(TABLE_NAME)

        # Prepare item for DynamoDB
        item = {
            "job_id": job_id,
            "status": state.get("status", "unknown"),
            "created_at": (
                state.get("created_at", datetime.now()).isoformat()
                if isinstance(state.get("created_at"), datetime)
                else state.get("created_at", datetime.now().isoformat())
            ),
            # TTL: auto-delete after 1 hour
            "ttl": int((datetime.now() + timedelta(hours=1)).timestamp()),
        }

        # Add progress if available
        if state.get("progress"):
            item["progress"] = json.dumps(state["progress"])

        # Add result if available
        if state.get("result"):
            result = state["result"].copy()
            # Document objects cannot be stored in DynamoDB
            # They should be stored in S3 separately
            if "document" in result:
                result.pop("document", None)
            item["result"] = json.dumps(result)

        # Add error if available
        if state.get("error"):
            item["error"] = str(state["error"])

        # Add delivery method and email if available
        if state.get("delivery_method"):
            item["delivery_method"] = state["delivery_method"]
        if state.get("email"):
            item["email"] = state["email"]

        # Store in DynamoDB
        table.put_item(Item=item)
        logger.info(
            "Stored job state",
            extra={"extra_fields": {"job_id": job_id, "status": state.get("status")}},
        )

    except Exception as e:
        logger.error(
            "Failed to store job state in DynamoDB",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        raise


def get_job_state(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve job state from DynamoDB.

    Fetches the current state of a pipeline job from DynamoDB and reconstructs
    the state dictionary with proper data types.

    Args:
        job_id: Unique job identifier (UUID string).

    Returns:
        Dictionary containing job state with keys:
            - status (str): Current job status
            - created_at (datetime): Job creation timestamp
            - progress (dict, optional): Current progress information
            - result (dict, optional): Result metadata (includes S3 key for document)
            - error (str, optional): Error message if job failed
        Returns None if job not found or if DynamoDB operation fails.

    Note:
        Progress and result fields are JSON-encoded in DynamoDB and are automatically
        decoded when retrieved.
    """
    try:
        dynamodb = get_dynamodb_resource()
        if dynamodb is None:
            logger.error(
                "DynamoDB resource not available",
                extra={
                    "extra_fields": {"job_id": job_id, "operation": "get_job_state"}
                },
            )
            return None

        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"job_id": job_id})

        if "Item" not in response:
            return None

        item = response["Item"]

        # Reconstruct state dictionary
        state = {
            "status": item.get("status", "unknown"),
            "created_at": (
                datetime.fromisoformat(item["created_at"])
                if "created_at" in item
                else datetime.now()
            ),
        }

        # Parse progress if available
        if "progress" in item:
            state["progress"] = json.loads(item["progress"])

        # Parse result if available
        if "result" in item:
            state["result"] = json.loads(item["result"])

        # Add error if available
        if "error" in item:
            state["error"] = item["error"]

        # Add delivery method and email if available
        if "delivery_method" in item:
            state["delivery_method"] = item["delivery_method"]
        if "email" in item:
            state["email"] = item["email"]

        return state

    except Exception as e:
        logger.error(
            "Failed to get job state from DynamoDB",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return None


def update_job_progress(job_id: str, progress: Dict) -> None:
    """Update job progress in DynamoDB.

    Updates only the progress field of a job state record without affecting
    other fields. Used during pipeline execution to provide real-time progress updates.

    Args:
        job_id: Unique job identifier (UUID string).
        progress: Progress dictionary containing:
            - phase (str): Current pipeline phase (e.g., "profiling", "searching", "scoring")
            - message (str): Human-readable progress message

    Note:
        This function uses DynamoDB's UpdateItem operation to update only the progress
        field, making it efficient for frequent progress updates during pipeline execution.
    """
    try:
        dynamodb = get_dynamodb_resource()
        if dynamodb is None:
            logger.error("DynamoDB resource not available")
            return

        table = dynamodb.Table(TABLE_NAME)

        progress_json = json.dumps(progress)
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #progress = :progress",
            ExpressionAttributeNames={"#progress": "progress"},
            ExpressionAttributeValues={":progress": progress_json},
        )

        logger.info(
            "Updated progress",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "phase": progress.get("phase"),
                    "message": progress.get("message"),
                    "progress_json": progress_json,
                }
            },
        )

    except Exception as e:
        logger.error(
            "Failed to update job progress in DynamoDB",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )


def get_cancellation_flag(job_id: str) -> bool:
    """Check if a job has been cancelled.

    Queries DynamoDB to determine if a job's status has been set to "cancelling"
    or "cancelled". Used by the pipeline to check for cancellation requests
    during long-running operations.

    Args:
        job_id: Unique job identifier (UUID string).

    Returns:
        True if job status is "cancelling" or "cancelled", False otherwise.
        Returns False if job not found or if DynamoDB operation fails.

    Note:
        This function is called frequently during pipeline execution to enable
        responsive cancellation. It uses a simple status check for efficiency.
    """
    try:
        dynamodb = get_dynamodb_resource()
        if dynamodb is None:
            return False

        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"job_id": job_id})

        if "Item" not in response:
            return False

        item = response["Item"]
        status = item.get("status", "")
        return status == "cancelling" or status == "cancelled"

    except Exception as e:
        logger.error(
            "Failed to check cancellation flag",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return False


def update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Update job status in DynamoDB.

    Updates the status and optionally the result or error fields of a job state record.
    Used to mark jobs as complete, failed, or cancelled.

    Args:
        job_id: Unique job identifier (UUID string).
        status: New job status. Valid values:
            - "running": Pipeline is currently executing
            - "complete": Pipeline finished successfully
            - "error": Pipeline encountered an error
            - "cancelled": Pipeline was cancelled by user
        result: Optional dictionary containing result metadata:
            - filename (str): Generated document filename
            - timestamp (str): Job timestamp
            - s3_key (str): S3 key where document is stored
        error: Optional error message string if job failed.

    Note:
        The result dictionary should not contain Document objects as they cannot
        be serialized to JSON. Only metadata should be included.
    """
    try:
        dynamodb = get_dynamodb_resource()
        if dynamodb is None:
            logger.error("DynamoDB resource not available")
            return

        table = dynamodb.Table(TABLE_NAME)

        update_expr = "SET #status = :status"
        expr_attrs = {"#status": "status"}
        expr_values = {":status": status}

        if result:
            # Store result metadata (without document object)
            result_clean = result.copy()
            result_clean.pop("document", None)
            update_expr += ", #result = :result"
            expr_attrs["#result"] = "result"
            expr_values[":result"] = json.dumps(result_clean)

        if error:
            update_expr += ", #error = :error"
            expr_attrs["#error"] = "error"
            expr_values[":error"] = error

        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attrs,
            ExpressionAttributeValues=expr_values,
        )

        logger.info(
            "Updated job status",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "status": status,
                    "has_result": bool(result),
                    "has_error": bool(error),
                }
            },
        )

    except Exception as e:
        logger.error(
            "Failed to update job status in DynamoDB",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "status": status,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
