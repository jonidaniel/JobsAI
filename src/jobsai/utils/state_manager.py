"""
State Management for Pipeline Jobs using DynamoDB and S3.

This module provides a unified interface for pipeline job state management.
It re-exports functions from focused modules (dynamodb_manager, s3_manager, presigned_urls)
to maintain backward compatibility with existing code.

For new code, consider importing directly from the focused modules:
- jobsai.utils.dynamodb_manager: DynamoDB operations
- jobsai.utils.s3_manager: S3 document storage
- jobsai.utils.presigned_urls: Presigned URL generation

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

# Re-export DynamoDB functions
from jobsai.utils.dynamodb_manager import (
    get_dynamodb_client,
    get_dynamodb_resource,
    store_job_state,
    get_job_state,
    update_job_progress,
    get_cancellation_flag,
    update_job_status,
)

# Re-export S3 functions
from jobsai.utils.s3_manager import (
    store_document_in_s3,
    get_document_from_s3,
)

# Re-export presigned URL functions
from jobsai.utils.presigned_urls import (
    get_presigned_s3_url,
)

# Re-export constants for backward compatibility
from jobsai.utils.dynamodb_manager import TABLE_NAME
from jobsai.utils.s3_manager import S3_BUCKET

__all__ = [
    # DynamoDB functions
    "get_dynamodb_client",
    "get_dynamodb_resource",
    "store_job_state",
    "get_job_state",
    "update_job_progress",
    "get_cancellation_flag",
    "update_job_status",
    # S3 functions
    "store_document_in_s3",
    "get_document_from_s3",
    # Presigned URL functions
    "get_presigned_s3_url",
    # Constants
    "TABLE_NAME",
    "S3_BUCKET",
]
