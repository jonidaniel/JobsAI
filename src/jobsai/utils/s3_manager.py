"""
S3 Manager for Document Storage.

This module handles all S3 operations for storing and retrieving pipeline documents.
Documents are stored in S3 since they cannot be stored in DynamoDB.

Environment Variables:
    S3_DOCUMENTS_BUCKET: Name of the S3 bucket for document storage

Note:
    All functions use lazy initialization for AWS clients to avoid import-time
    dependencies and support local development without AWS credentials.
"""

import os
from typing import Optional, Any
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)

# S3 bucket for storing documents (set via environment variable)
S3_BUCKET = os.environ.get("S3_DOCUMENTS_BUCKET", None)


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
