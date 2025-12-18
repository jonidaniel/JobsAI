"""
Lambda Worker Invocation Handler.

Handles asynchronous invocation of the worker Lambda function to run the pipeline.
"""

import json
import os
from jobsai.config.schemas import FrontendPayload
from jobsai.utils.logger import get_logger, log_performance

logger = get_logger(__name__)


def invoke_worker_lambda(job_id: str, payload: FrontendPayload) -> None:
    """Invoke Lambda worker function asynchronously to run the pipeline.

    Uses AWS Lambda's asynchronous invocation (InvocationType="Event") to start
    the pipeline in a separate Lambda invocation. This ensures the pipeline can
    run for up to 15 minutes without blocking the API response.

    The worker Lambda receives the job_id and payload, executes the pipeline,
    and updates progress in DynamoDB throughout execution.

    Args:
        job_id: Unique job identifier (UUID string) for this pipeline run.
        payload: FrontendPayload object containing validated form data.

    Raises:
        RuntimeError: If boto3 is not available (should not happen in Lambda).
        Exception: If Lambda invocation fails (permissions, function not found, etc.).

    Note:
        The function name is determined by the WORKER_LAMBDA_FUNCTION_NAME environment
        variable, with fallback to LAMBDA_FUNCTION_NAME (same function, different handler).
        The invocation is asynchronous, so this function returns immediately after
        queuing the invocation request.
    """
    try:
        import boto3

        lambda_client = boto3.client("lambda")
        worker_function_name = os.environ.get(
            "WORKER_LAMBDA_FUNCTION_NAME", os.environ.get("LAMBDA_FUNCTION_NAME")
        )

        # Prepare event payload
        event_payload = {
            "job_id": job_id,
            "payload": payload.model_dump(by_alias=True),
        }

        # Invoke Lambda asynchronously (Event invocation type)
        with log_performance(
            "invoke_worker_lambda", job_id=job_id, function_name=worker_function_name
        ):
            response = lambda_client.invoke(
                FunctionName=worker_function_name,
                InvocationType="Event",  # Async invocation
                Payload=json.dumps(event_payload),
            )

        logger.info(
            "Worker Lambda invoked successfully",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "function_name": worker_function_name,
                    "status_code": response.get("StatusCode"),
                }
            },
        )

    except ImportError:
        logger.error(
            "boto3 not available",
            extra={"extra_fields": {"job_id": job_id, "error": "ImportError"}},
        )
        raise RuntimeError("boto3 not available")
    except Exception as e:
        logger.error(
            "Failed to invoke worker Lambda",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "function_name": worker_function_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        raise
