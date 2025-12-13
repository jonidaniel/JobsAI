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
import logging
from jobsai.main import main
from jobsai.utils.state_manager import (
    update_job_progress,
    update_job_status,
    store_job_state,
    store_document_in_s3,
    get_cancellation_flag,
)
from jobsai.config.schemas import FrontendPayload
from jobsai.utils.exceptions import CancellationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


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


def worker_handler(event, context):
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
    try:
        logger.info(f"Worker handler invoked with event: {json.dumps(event)}")

        # Extract job_id and payload from event
        job_id = event.get("job_id")
        payload_data = event.get("payload")

        if not job_id:
            logger.error("Missing job_id in event")
            return {"statusCode": 400, "body": "Missing job_id"}

        if not payload_data:
            logger.error("Missing payload in event")
            return {"statusCode": 400, "body": "Missing payload"}

        logger.info(f"Processing pipeline for job_id: {job_id}")

        # Convert payload dict to FrontendPayload model
        payload = FrontendPayload(**payload_data)

        # Define progress callback that updates DynamoDB
        def progress_callback(phase: str, message: str):
            logger.info(f"Progress update - {phase}: {message}")
            update_job_progress(job_id, {"phase": phase, "message": message})

        # Define cancellation check that reads from DynamoDB
        def cancellation_check() -> bool:
            return get_cancellation_flag(job_id)

        # Run the pipeline
        logger.info(f"Starting pipeline execution for job_id: {job_id}")
        result = main(
            payload.model_dump(by_alias=True), progress_callback, cancellation_check
        )

        # Store documents in S3 and prepare result data
        s3_keys, result_data = _store_documents_and_prepare_result(job_id, result)

        update_job_status(job_id, "complete", result=result_data)

        logger.info(f"Pipeline completed successfully for job_id: {job_id}")
        return {"statusCode": 200, "body": "Pipeline completed"}

    except CancellationError:
        logger.info(f"Pipeline cancelled for job_id: {job_id}")
        update_job_status(job_id, "cancelled")
        return {"statusCode": 200, "body": "Pipeline cancelled"}

    except Exception as e:
        logger.error(f"Pipeline failed for job_id: {job_id}: {str(e)}", exc_info=True)
        update_job_status(job_id, "error", error=str(e))
        return {"statusCode": 500, "body": f"Pipeline failed: {str(e)}"}
