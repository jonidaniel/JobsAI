"""
State Management for Pipeline Jobs using DynamoDB and S3.

This module provides functions to store and retrieve pipeline job state from DynamoDB,
ensuring state persists across Lambda invocations and containers. Documents are stored
in S3 since they cannot be stored in DynamoDB.

The module handles:
- Job state persistence (status, progress, results, errors)
- Document storage and retrieval from S3
- Presigned URL generation for secure document downloads
- Cancellation flag management

Environment Variables:
    DYNAMODB_TABLE_NAME: Name of the DynamoDB table (default: "jobsai-pipeline-states")
    S3_DOCUMENTS_BUCKET: Name of the S3 bucket for document storage

Note:
    All functions use lazy initialization for AWS clients to avoid import-time
    dependencies and support local development without AWS credentials.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)

# DynamoDB table name (set via environment variable or use default)
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "jobsai-pipeline-states")

# S3 bucket for storing documents (set via environment variable)
S3_BUCKET = os.environ.get("S3_DOCUMENTS_BUCKET", None)

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
        in S3 using store_document_in_s3().
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

        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #progress = :progress",
            ExpressionAttributeNames={"#progress": "progress"},
            ExpressionAttributeValues={":progress": json.dumps(progress)},
        )

        logger.info(
            "Updated progress",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "phase": progress.get("phase"),
                    "message": progress.get("message"),
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


def store_document_in_s3(job_id: str, document: Any, filename: str) -> Optional[str]:
    """Store document in S3 and return the S3 key.

    Converts a python-docx Document object to bytes and uploads it to S3.
    The document is stored in a structured path: documents/{job_id}/{filename}

    Args:
        job_id: Unique job identifier (UUID string).
        document: python-docx Document object to store.
        filename: Filename for the document (e.g., "20250115_143022_cover_letter.docx").

    Returns:
        S3 key (string path) where document is stored, or None if storage fails.
        Format: "documents/{job_id}/{filename}"

    Raises:
        Exception: If S3 upload fails or boto3 is not available.

    Note:
        The document is stored with the correct Content-Type header for Word documents.
        This ensures proper handling when downloading from S3.
    """
    try:
        import boto3
        from io import BytesIO

        if not S3_BUCKET:
            logger.warning(
                "S3_BUCKET not configured",
                extra={"extra_fields": {"job_id": job_id, "filename": filename}},
            )
            return None

        s3_client = boto3.client("s3")
        s3_key = f"documents/{job_id}/{filename}"

        # Convert document to bytes
        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=buffer.getvalue(),
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        logger.info(
            "Stored document in S3",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "filename": filename,
                    "s3_key": s3_key,
                    "s3_bucket": S3_BUCKET,
                }
            },
        )
        return s3_key

    except Exception as e:
        logger.error(
            "Failed to store document in S3",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "filename": filename,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return None


def get_presigned_s3_url(s3_key: str, expiration: int = 3600) -> Optional[str]:
    """Generate a presigned URL for downloading a document from S3.

    Creates a time-limited, signed URL that allows direct download from S3 without
    requiring AWS credentials. This bypasses API Gateway binary encoding issues.

    Args:
        s3_key: S3 key (path) of the document (e.g., "documents/{job_id}/{filename}").
        expiration: URL expiration time in seconds. Default is 3600 (1 hour).
            Maximum is 604800 (7 days) for presigned URLs.

    Returns:
        Presigned URL string that can be used to download the document directly
        from S3, or None if URL generation fails.

    Note:
        The presigned URL includes ResponseContentType and ResponseContentDisposition
        headers to ensure the browser handles the download correctly. The URL is
        cryptographically signed and cannot be modified without invalidating it.
    """
    try:
        import boto3

        if not S3_BUCKET or not s3_key:
            logger.warning(
                "S3_BUCKET or s3_key not set",
                extra={
                    "extra_fields": {
                        "s3_bucket": S3_BUCKET,
                        "s3_key": s3_key,
                    }
                },
            )
            return None

        s3_client = boto3.client("s3")
        logger.info(
            "Generating presigned URL",
            extra={
                "extra_fields": {
                    "s3_bucket": S3_BUCKET,
                    "s3_key": s3_key,
                    "expiration_seconds": expiration,
                }
            },
        )

        # Extract filename from S3 key (last part after /)
        filename_from_key = s3_key.split("/")[-1]

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": s3_key,
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                # Use simple filename without quotes to avoid encoding issues
                "ResponseContentDisposition": f"attachment; filename={filename_from_key}",
            },
            ExpiresIn=expiration,
        )

        logger.info(
            "Generated presigned URL",
            extra={
                "extra_fields": {
                    "s3_key": s3_key,
                    "expiration_seconds": expiration,
                }
            },
        )
        return url

    except Exception as e:
        logger.error(
            "Failed to generate presigned S3 URL",
            extra={
                "extra_fields": {
                    "s3_key": s3_key,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return None


def get_document_from_s3(s3_key: str) -> Optional[bytes]:
    """Retrieve document bytes from S3.

    Downloads a document from S3 and returns its raw bytes. This is used as a
    fallback when presigned URLs are not available (e.g., for legacy endpoints).

    Args:
        s3_key: S3 key (path) of the document (e.g., "documents/{job_id}/{filename}").

    Returns:
        Raw document bytes as a bytes object, or None if retrieval fails.
        The bytes can be used directly in HTTP responses or converted to a Blob.

    Note:
        This function reads the entire document into memory. For large documents,
        consider using presigned URLs instead to allow direct browser downloads.
    """
    try:
        import boto3

        if not S3_BUCKET or not s3_key:
            logger.warning(
                "S3_BUCKET or s3_key not set",
                extra={
                    "extra_fields": {
                        "s3_bucket": S3_BUCKET,
                        "s3_key": s3_key,
                    }
                },
            )
            return None

        s3_client = boto3.client("s3")
        logger.info(
            "Retrieving document from S3",
            extra={
                "extra_fields": {
                    "s3_bucket": S3_BUCKET,
                    "s3_key": s3_key,
                }
            },
        )
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)

        # Read all bytes from the response body
        document_bytes = response["Body"].read()
        logger.info(
            "Retrieved document from S3",
            extra={
                "extra_fields": {
                    "s3_key": s3_key,
                    "bytes": len(document_bytes),
                }
            },
        )
        return document_bytes

    except Exception as e:
        logger.error(
            "Failed to get document from S3",
            extra={
                "extra_fields": {
                    "s3_key": s3_key,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return None


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
