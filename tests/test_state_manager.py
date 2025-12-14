# ---------- TESTS FOR STATE MANAGER ----------

import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from docx import Document

from jobsai.utils.state_manager import (
    store_job_state,
    get_job_state,
    update_job_progress,
    store_document_in_s3,
    get_presigned_s3_url,
    get_document_from_s3,
    get_cancellation_flag,
    update_job_status,
)


# Mock DynamoDB table
@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = MagicMock()
    table.put_item = MagicMock()
    table.get_item = MagicMock(return_value={"Item": {}})
    table.update_item = MagicMock()
    return table


# Mock DynamoDB resource
@pytest.fixture
def mock_dynamodb_resource(mock_dynamodb_table):
    """Create a mock DynamoDB resource."""
    resource = MagicMock()
    resource.Table = MagicMock(return_value=mock_dynamodb_table)
    return resource


# Mock S3 client
@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = MagicMock()
    client.put_object = MagicMock()
    client.generate_presigned_url = MagicMock(
        return_value="https://s3.amazonaws.com/bucket/key?signature=xyz"
    )
    client.get_object = MagicMock(
        return_value={"Body": MagicMock(read=MagicMock(return_value=b"test content"))}
    )
    return client


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_store_job_state_basic(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test storing job state in DynamoDB."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    job_id = "test-job-123"
    state = {
        "status": "running",
        "progress": {"phase": "profiling", "message": "Creating profile..."},
        "created_at": datetime.now(),
    }

    store_job_state(job_id, state)

    # Verify put_item was called
    assert mock_dynamodb_table.put_item.called
    call_args = mock_dynamodb_table.put_item.call_args
    item = call_args[1]["Item"]
    assert item["job_id"] == job_id
    assert item["status"] == "running"
    assert "ttl" in item  # TTL should be set


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_get_job_state_basic(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test retrieving job state from DynamoDB."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    # Mock DynamoDB response
    created_at = datetime.now().isoformat()
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "job_id": "test-job-123",
            "status": "complete",
            "created_at": created_at,
            "progress": json.dumps({"phase": "generating", "message": "Done"}),
            "result": json.dumps({"filename": "cover_letter.docx"}),
        }
    }

    state = get_job_state("test-job-123")

    assert state is not None
    assert state["status"] == "complete"
    assert "progress" in state
    assert "result" in state


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_get_job_state_not_found(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test retrieving non-existent job state."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    # Mock empty response
    mock_dynamodb_table.get_item.return_value = {}

    state = get_job_state("non-existent-job")
    assert state is None


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_update_job_progress(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test updating job progress."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    job_id = "test-job-123"
    progress = {"phase": "searching", "message": "Searching for jobs..."}

    update_job_progress(job_id, progress)

    # Verify update_item was called
    assert mock_dynamodb_table.update_item.called
    call_args = mock_dynamodb_table.update_item.call_args
    assert call_args[0][0]["job_id"] == job_id


@patch("jobsai.utils.state_manager.boto3")
@patch.dict("os.environ", {"S3_DOCUMENTS_BUCKET": "test-bucket"})
def test_store_document_in_s3(mock_boto3, mock_s3_client):
    """Test storing document in S3."""
    mock_boto3.client.return_value = mock_s3_client

    job_id = "test-job-123"
    document = Document()
    filename = "cover_letter.docx"

    s3_key = store_document_in_s3(job_id, document, filename)

    assert s3_key is not None
    assert s3_key.startswith("documents/")
    assert job_id in s3_key
    assert filename in s3_key
    # Verify put_object was called
    assert mock_s3_client.put_object.called


@patch("jobsai.utils.state_manager.boto3")
@patch.dict("os.environ", {"S3_DOCUMENTS_BUCKET": "test-bucket"})
def test_get_presigned_s3_url(mock_boto3, mock_s3_client):
    """Test generating presigned S3 URL."""
    mock_boto3.client.return_value = mock_s3_client

    s3_key = "documents/test-job-123/cover_letter.docx"
    url = get_presigned_s3_url(s3_key)

    assert url is not None
    assert "s3" in url.lower() or "amazonaws" in url.lower()
    # Verify generate_presigned_url was called
    assert mock_s3_client.generate_presigned_url.called


@patch("jobsai.utils.state_manager.boto3")
@patch.dict("os.environ", {"S3_DOCUMENTS_BUCKET": "test-bucket"})
def test_get_document_from_s3(mock_boto3, mock_s3_client):
    """Test retrieving document from S3."""
    mock_boto3.client.return_value = mock_s3_client

    s3_key = "documents/test-job-123/cover_letter.docx"
    document_bytes = get_document_from_s3(s3_key)

    assert document_bytes is not None
    assert isinstance(document_bytes, bytes)
    # Verify get_object was called
    assert mock_s3_client.get_object.called


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_get_cancellation_flag_true(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test cancellation flag when job is cancelled."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    mock_dynamodb_table.get_item.return_value = {
        "Item": {"job_id": "test-job-123", "status": "cancelling"}
    }

    is_cancelled = get_cancellation_flag("test-job-123")
    assert is_cancelled is True


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_get_cancellation_flag_false(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test cancellation flag when job is not cancelled."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    mock_dynamodb_table.get_item.return_value = {
        "Item": {"job_id": "test-job-123", "status": "running"}
    }

    is_cancelled = get_cancellation_flag("test-job-123")
    assert is_cancelled is False


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_update_job_status(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test updating job status."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    job_id = "test-job-123"
    result = {
        "filename": "cover_letter.docx",
        "s3_key": "documents/test/cover_letter.docx",
    }

    update_job_status(job_id, "complete", result=result)

    # Verify update_item was called
    assert mock_dynamodb_table.update_item.called
    call_args = mock_dynamodb_table.update_item.call_args
    assert call_args[0][0]["job_id"] == job_id


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_update_job_status_with_error(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test updating job status with error."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    job_id = "test-job-123"
    error = "Pipeline failed: Test error"

    update_job_status(job_id, "error", error=error)

    # Verify update_item was called
    assert mock_dynamodb_table.update_item.called
    call_args = mock_dynamodb_table.update_item.call_args
    # Check that error is in the update expression values
    expr_values = call_args[1]["ExpressionAttributeValues"]
    assert ":error" in expr_values
    assert expr_values[":error"] == error


@patch("jobsai.utils.state_manager.get_dynamodb_resource")
def test_store_job_state_handles_missing_result(
    mock_get_resource, mock_dynamodb_resource, mock_dynamodb_table
):
    """Test storing job state without result."""
    mock_get_resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_dynamodb_table

    job_id = "test-job-123"
    state = {
        "status": "running",
        "created_at": datetime.now(),
    }

    store_job_state(job_id, state)

    # Should still work without result
    assert mock_dynamodb_table.put_item.called
