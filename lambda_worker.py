"""
Lambda worker handler for pipeline execution.

This handler is invoked asynchronously to run the pipeline.
It reads job data from the event, executes the pipeline, and stores results in DynamoDB.
"""

import json
import logging
from jobsai.main import main
from jobsai.utils.state_manager import (
    update_job_progress,
    update_job_status,
    store_job_state,
    store_document_in_s3,
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


def worker_handler(event, context):
    """
    Lambda worker handler for pipeline execution.

    This function is invoked asynchronously by the main Lambda function.
    It runs the pipeline and updates state in DynamoDB.

    Args:
        event: Lambda event containing:
            - job_id: Job identifier
            - payload: FrontendPayload data (as dict)
        context: Lambda context

    Returns:
        dict: Result status
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

        # Define cancellation check (for future use)
        def cancellation_check() -> bool:
            # TODO: Check DynamoDB for cancellation flag
            return False

        # Run the pipeline
        logger.info(f"Starting pipeline execution for job_id: {job_id}")
        result = main(
            payload.model_dump(by_alias=True), progress_callback, cancellation_check
        )

        # Store document in S3
        document = result.get("document")
        filename = result.get("filename", "cover_letter.docx")
        s3_key = None

        if document:
            s3_key = store_document_in_s3(job_id, document, filename)
            if not s3_key:
                logger.warning(f"Failed to store document in S3 for job_id: {job_id}")

        # Store result in DynamoDB (without document object)
        update_job_status(
            job_id,
            "complete",
            result={
                "filename": filename,
                "timestamp": result.get("timestamp"),
                "s3_key": s3_key,  # Store S3 key for retrieval
            },
        )

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
