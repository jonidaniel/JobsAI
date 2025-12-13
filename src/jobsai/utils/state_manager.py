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
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union

logger = logging.getLogger(__name__)

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
            logger.warning("boto3 not available, DynamoDB operations will fail")
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
            logger.warning("boto3 not available, DynamoDB operations will fail")
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

        # Store in DynamoDB
        table.put_item(Item=item)
        logger.info(f"Stored job state for job_id: {job_id} in DynamoDB")

    except Exception as e:
        logger.error(f"Failed to store job state in DynamoDB: {str(e)}", exc_info=True)
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
            logger.error("DynamoDB resource not available")
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

        return state

    except Exception as e:
        logger.error(f"Failed to get job state from DynamoDB: {str(e)}", exc_info=True)
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

        logger.info(f"Updated progress for job_id: {job_id} in DynamoDB")

    except Exception as e:
        logger.error(
            f"Failed to update job progress in DynamoDB: {str(e)}", exc_info=True
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
            logger.warning("S3_BUCKET not configured, cannot store document")
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

        logger.info(f"Stored document in S3: s3://{S3_BUCKET}/{s3_key}")
        return s3_key

    except Exception as e:
        logger.error(f"Failed to store document in S3: {str(e)}", exc_info=True)
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
                f"S3_BUCKET or s3_key not set. S3_BUCKET: {S3_BUCKET}, s3_key: {s3_key}"
            )
            return None

        s3_client = boto3.client("s3")
        logger.info(f"Generating presigned URL for S3: s3://{S3_BUCKET}/{s3_key}")

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

        logger.info(f"Generated presigned URL (expires in {expiration}s)")
        return url

    except Exception as e:
        logger.error(f"Failed to generate presigned S3 URL: {str(e)}", exc_info=True)
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
                f"S3_BUCKET or s3_key not set. S3_BUCKET: {S3_BUCKET}, s3_key: {s3_key}"
            )
            return None

        s3_client = boto3.client("s3")
        logger.info(f"Retrieving document from S3: s3://{S3_BUCKET}/{s3_key}")
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)

        # Read all bytes from the response body
        document_bytes = response["Body"].read()
        logger.info(f"Retrieved {len(document_bytes)} bytes from S3")
        return document_bytes

    except Exception as e:
        logger.error(f"Failed to get document from S3: {str(e)}", exc_info=True)
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
        logger.error(f"Failed to check cancellation flag: {str(e)}", exc_info=True)
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

        logger.info(f"Updated job status for job_id: {job_id} to {status} in DynamoDB")

    except Exception as e:
        logger.error(
            f"Failed to update job status in DynamoDB: {str(e)}", exc_info=True
        )
