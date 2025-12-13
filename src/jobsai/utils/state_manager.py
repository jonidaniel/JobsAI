"""
State management for pipeline jobs using DynamoDB and S3.

This module provides functions to store and retrieve pipeline job state
from DynamoDB, ensuring state persists across Lambda invocations and containers.
Documents are stored in S3 since they cannot be stored in DynamoDB.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# DynamoDB table name (set via environment variable or use default)
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "jobsai-pipeline-states")

# S3 bucket for storing documents (set via environment variable)
S3_BUCKET = os.environ.get("S3_DOCUMENTS_BUCKET", None)

# Initialize DynamoDB client (lazy initialization)
_dynamodb_client = None
_dynamodb_resource = None


def get_dynamodb_client():
    """Get or create DynamoDB client (lazy initialization)."""
    global _dynamodb_client
    if _dynamodb_client is None:
        try:
            import boto3

            _dynamodb_client = boto3.client("dynamodb")
        except ImportError:
            logger.warning("boto3 not available, DynamoDB operations will fail")
            _dynamodb_client = None
    return _dynamodb_client


def get_dynamodb_resource():
    """Get or create DynamoDB resource (lazy initialization)."""
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
    """
    Store job state in DynamoDB.

    Args:
        job_id: Job identifier
        state: State dictionary containing status, progress, result, error, created_at
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


def get_job_state(job_id: str) -> Optional[Dict]:
    """
    Retrieve job state from DynamoDB.

    Args:
        job_id: Job identifier

    Returns:
        State dictionary or None if not found
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
    """
    Update job progress in DynamoDB.

    Args:
        job_id: Job identifier
        progress: Progress dictionary with phase and message
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


def store_document_in_s3(job_id: str, document, filename: str) -> str:
    """
    Store document in S3 and return the S3 key.

    Args:
        job_id: Job identifier
        document: python-docx Document object
        filename: Filename for the document

    Returns:
        S3 key (path) where document is stored
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
    """
    Generate a presigned URL for downloading a document from S3.

    Args:
        s3_key: S3 key (path) of the document
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string, or None if error
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

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": s3_key,
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "ResponseContentDisposition": f'attachment; filename="{s3_key.split("/")[-1]}"',
            },
            ExpiresIn=expiration,
        )

        logger.info(f"Generated presigned URL (expires in {expiration}s)")
        return url

    except Exception as e:
        logger.error(f"Failed to generate presigned S3 URL: {str(e)}", exc_info=True)
        return None


def get_document_from_s3(s3_key: str) -> Optional[bytes]:
    """
    Retrieve document from S3.

    Args:
        s3_key: S3 key (path) of the document

    Returns:
        bytes: Document bytes, or None if not found
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
    """
    Check if a job has been cancelled.

    Args:
        job_id: Job identifier

    Returns:
        True if job is cancelled, False otherwise
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
    job_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None
) -> None:
    """
    Update job status in DynamoDB.

    Args:
        job_id: Job identifier
        status: New status (running, complete, error, cancelled)
        result: Optional result dictionary
        error: Optional error message
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
