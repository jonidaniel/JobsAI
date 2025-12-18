"""
Presigned URL Generator for S3 Documents.

This module generates time-limited, signed URLs that allow direct download from S3
without requiring AWS credentials. This bypasses API Gateway binary encoding issues.

Environment Variables:
    S3_DOCUMENTS_BUCKET: Name of the S3 bucket for document storage
"""

import os
from typing import Optional
from jobsai.utils.logger import get_logger

logger = get_logger(__name__)

# S3 bucket for storing documents (set via environment variable)
S3_BUCKET = os.environ.get("S3_DOCUMENTS_BUCKET", None)


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
