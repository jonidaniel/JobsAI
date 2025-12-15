"""
Lambda Worker Handler for Asynchronous Pipeline Execution.

This module provides the worker Lambda handler that executes the JobsAI pipeline
asynchronously. It is invoked by the main Lambda function using async invocation
to ensure long-running pipelines don't block API requests.

The worker:
1. Receives job data from the Lambda event
2. Executes the complete pipeline (profiling, searching, scoring, analyzing, generating)
3. Stores the generated document in S3
4. Updates job state in DynamoDB with progress and results

This separation allows the API to respond immediately while the pipeline runs
in a separate Lambda invocation that can run for up to 15 minutes.

Note:
    This handler is invoked asynchronously (InvocationType="Event"), so it does
    not return a response to the caller. All communication happens through DynamoDB
    state updates that the API polls via /api/progress endpoint.
"""

import json
from typing import Any, Dict, Tuple, List
from jobsai.main import main
from jobsai.utils.state_manager import (
    update_job_progress,
    update_job_status,
    store_job_state,
    store_document_in_s3,
    get_cancellation_flag,
    get_job_state,
)
from jobsai.config.schemas import FrontendPayload
from jobsai.utils.exceptions import CancellationError
from jobsai.utils.logger import (
    configure_logging,
    get_logger,
    set_correlation_id,
    log_performance,
)

logger = get_logger(__name__)


def _store_documents_and_prepare_result(
    job_id: str, result: dict
) -> tuple[list[str], dict]:
    """Store documents in S3 and prepare result data for DynamoDB.

    Handles both single document (backward compatibility) and multiple documents.
    Stores each document in S3 and returns S3 keys along with result metadata.

    Args:
        job_id: Unique job identifier (UUID string).
        result: Pipeline result dictionary containing documents and metadata.

    Returns:
        Tuple of (s3_keys, result_data):
            - s3_keys: List of S3 keys for stored documents
            - result_data: Dictionary with timestamp, filenames/s3_keys, and count
    """
    documents = result.get("documents")
    document = result.get("document")  # Single document (backward compatibility)
    filenames = result.get("filenames", [])
    filename = result.get(
        "filename", "cover_letter.docx"
    )  # Single filename (backward compatibility)

    s3_keys = []

    if documents:
        # Multiple documents - store each one
        for idx, doc in enumerate(documents):
            doc_filename = (
                filenames[idx]
                if idx < len(filenames)
                else f"cover_letter_{idx + 1}.docx"
            )
            s3_key = store_document_in_s3(job_id, doc, doc_filename)
            if s3_key:
                s3_keys.append(s3_key)
            else:
                logger.warning(
                    f"Failed to store document {idx + 1} in S3 for job_id: {job_id}"
                )
    elif document:
        # Single document (backward compatibility)
        s3_key = store_document_in_s3(job_id, document, filename)
        if s3_key:
            s3_keys.append(s3_key)
        else:
            logger.warning(f"Failed to store document in S3 for job_id: {job_id}")

    # Prepare result data for DynamoDB
    result_data = {"timestamp": result.get("timestamp")}

    if documents and filenames:
        # Multiple documents
        result_data["filenames"] = filenames
        result_data["s3_keys"] = s3_keys
        result_data["count"] = len(documents)
    else:
        # Single document (backward compatibility)
        result_data["filename"] = filename
        result_data["s3_key"] = s3_keys[0] if s3_keys else None

    return s3_keys, result_data


def worker_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda worker handler for asynchronous pipeline execution.

    Executes the complete JobsAI pipeline for a given job, updating progress in
    DynamoDB throughout execution. Stores the final document in S3 and updates
    the job status to "complete", "error", or "cancelled".

    Args:
        event: Lambda event dictionary containing:
            - job_id (str): Unique job identifier (UUID)
            - payload (dict): FrontendPayload data as dictionary (will be validated)
        context: Lambda context object (unused but required by Lambda interface).

    Returns:
        dict: Response dictionary with statusCode and body:
            - statusCode 200: Pipeline completed or cancelled successfully
            - statusCode 400: Missing required fields (job_id or payload)
            - statusCode 500: Pipeline execution failed

    Raises:
        CancellationError: If pipeline is cancelled during execution (handled internally).

    Note:
        This function is called asynchronously, so the return value is not used by
        the caller. All state updates happen through DynamoDB, which the API polls.
        Progress updates are written to DynamoDB via the progress_callback function.
    """
    # Configure logging with Lambda context
    configure_logging(context)

    try:
        # Extract job_id and payload from event
        job_id = event.get("job_id")
        payload_data = event.get("payload")

        # Set correlation ID for tracing
        set_correlation_id(
            request_id=context.aws_request_id if context else None, job_id=job_id
        )

        logger.info(
            "Worker handler invoked",
            extra={
                "extra_fields": {"job_id": job_id, "has_payload": bool(payload_data)}
            },
        )

        if not job_id:
            logger.error(
                "Missing job_id in event",
                extra={"extra_fields": {"event_keys": list(event.keys())}},
            )
            return {"statusCode": 400, "body": "Missing job_id"}

        if not payload_data:
            logger.error(
                "Missing payload in event", extra={"extra_fields": {"job_id": job_id}}
            )
            return {"statusCode": 400, "body": "Missing payload"}

        logger.info("Processing pipeline", extra={"extra_fields": {"job_id": job_id}})

        # Convert payload dict to FrontendPayload model
        payload = FrontendPayload(**payload_data)

        # Define progress callback that updates DynamoDB
        def progress_callback(phase: str, message: str):
            logger.info(
                "Progress update",
                extra={
                    "extra_fields": {
                        "job_id": job_id,
                        "phase": phase,
                        "message": message,
                    }
                },
            )
            update_job_progress(job_id, {"phase": phase, "message": message})

        # Define cancellation check that reads from DynamoDB
        def cancellation_check() -> bool:
            return get_cancellation_flag(job_id)

        # Run the pipeline with performance logging
        with log_performance("pipeline_execution", job_id=job_id):
            result = main(
                payload.model_dump(by_alias=True), progress_callback, cancellation_check
            )

        # Store documents in S3 and prepare result data
        with log_performance("store_documents", job_id=job_id):
            s3_keys, result_data = _store_documents_and_prepare_result(job_id, result)

        # Get job state to check delivery method
        job_state = get_job_state(job_id)
        delivery_method = job_state.get("delivery_method") if job_state else None
        email = job_state.get("email") if job_state else None

        # Send email if delivery method is email
        if delivery_method == "email" and email and s3_keys:
            from jobsai.utils.email_service import send_cover_letters_email

            filenames = result_data.get("filenames", [])
            if not filenames and result_data.get("filename"):
                # Single document (backward compatibility)
                filenames = [result_data.get("filename")]

            logger.info(
                "Sending cover letters via email",
                extra={
                    "extra_fields": {
                        "job_id": job_id,
                        "recipient_email_hash": (
                            email[:3] + "***@" + email.split("@")[1]
                            if "@" in email
                            else "***"
                        ),
                        "attachment_count": len(filenames),
                    }
                },
            )

            email_sent = send_cover_letters_email(
                recipient_email=email,
                job_id=job_id,
                s3_keys=s3_keys,
                filenames=filenames,
            )

            if not email_sent:
                logger.warning(
                    "Email delivery failed, but documents are available in S3",
                    extra={
                        "extra_fields": {
                            "job_id": job_id,
                            "recipient_email_hash": (
                                email[:3] + "***@" + email.split("@")[1]
                                if "@" in email
                                else "***"
                            ),
                        }
                    },
                )
                # Still mark as complete - documents are in S3
                # User can download manually if needed

        update_job_status(job_id, "complete", result=result_data)

        logger.info(
            "Pipeline completed successfully",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "documents_count": len(s3_keys) if s3_keys else 0,
                    "status": "complete",
                }
            },
        )
        return {"statusCode": 200, "body": "Pipeline completed"}

    except CancellationError:
        logger.info(
            "Pipeline cancelled",
            extra={"extra_fields": {"job_id": job_id, "status": "cancelled"}},
        )
        update_job_status(job_id, "cancelled")
        return {"statusCode": 200, "body": "Pipeline cancelled"}

    except Exception as e:
        logger.error(
            "Pipeline failed",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        update_job_status(job_id, "error", error=str(e))
        return {"statusCode": 500, "body": f"Pipeline failed: {str(e)}"}
