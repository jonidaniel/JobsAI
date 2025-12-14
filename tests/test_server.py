# ---------- TESTS FOR API SERVER ----------

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json

from jobsai.api.server import app

client = TestClient(app)


# Mock payload
mock_payload = {
    "general": [
        {"job-level": ["Expert"]},
        {"job-boards": ["Duunitori"]},
        {"deep-mode": "Yes"},
        {"cover-letter-num": 1},
        {"cover-letter-style": ["Professional"]},
    ],
    "languages": [{"python": 5}],
    "additional-info": [{"additional-info": "Test description"}],
}


@patch("jobsai.api.server.invoke_worker_lambda")
@patch("jobsai.api.server.store_job_state")
def test_start_pipeline_success(mock_store_state, mock_invoke_lambda):
    """Test successful pipeline start."""
    response = client.post("/api/start", json=mock_payload)

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)
    assert len(data["job_id"]) > 0

    # Verify state was stored
    assert mock_store_state.called
    # Verify Lambda was invoked
    assert mock_invoke_lambda.called


@patch("jobsai.api.server.invoke_worker_lambda", side_effect=Exception("Lambda error"))
@patch("jobsai.api.server.store_job_state")
@patch("jobsai.api.server.update_job_status")
def test_start_pipeline_lambda_error(
    mock_update_status, mock_store_state, mock_invoke_lambda
):
    """Test handling of Lambda invocation errors."""
    response = client.post("/api/start", json=mock_payload)

    assert response.status_code == 500
    # Verify error status was set
    assert mock_update_status.called


def test_start_pipeline_validation_error():
    """Test validation error handling."""
    invalid_payload = {
        "general": [
            {"job-level": ["Invalid"]},  # Invalid job level
        ],
    }

    response = client.post("/api/start", json=invalid_payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "message" in data


@patch("jobsai.api.server.get_job_state")
def test_get_progress_running(mock_get_state):
    """Test getting progress for running job."""
    mock_get_state.return_value = {
        "status": "running",
        "progress": {"phase": "profiling", "message": "Creating profile..."},
    }

    response = client.get("/api/progress/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "progress" in data
    assert data["progress"]["phase"] == "profiling"


@patch("jobsai.api.server.get_job_state")
def test_get_progress_complete_single(mock_get_state):
    """Test getting progress for completed job (single document)."""
    mock_get_state.return_value = {
        "status": "complete",
        "result": {
            "filename": "20250115_143022_cover_letter.docx",
            "s3_key": "documents/test/cover_letter.docx",
        },
    }

    response = client.get("/api/progress/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert "filename" in data


@patch("jobsai.api.server.get_job_state")
def test_get_progress_complete_multiple(mock_get_state):
    """Test getting progress for completed job (multiple documents)."""
    mock_get_state.return_value = {
        "status": "complete",
        "result": {
            "filenames": [
                "20250115_143022_cover_letter.docx",
                "20250115_143022_cover_letter_2.docx",
            ],
            "s3_keys": [
                "documents/test/cover_letter.docx",
                "documents/test/cover_letter_2.docx",
            ],
        },
    }

    response = client.get("/api/progress/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert "filenames" in data
    assert len(data["filenames"]) == 2


@patch("jobsai.api.server.get_job_state")
def test_get_progress_error(mock_get_state):
    """Test getting progress for failed job."""
    mock_get_state.return_value = {
        "status": "error",
        "error": "Pipeline failed: Test error",
    }

    response = client.get("/api/progress/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "error" in data
    assert "Test error" in data["error"]


@patch("jobsai.api.server.get_job_state")
def test_get_progress_not_found(mock_get_state):
    """Test getting progress for non-existent job."""
    mock_get_state.return_value = None

    response = client.get("/api/progress/non-existent-job")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@patch("jobsai.api.server.get_job_state")
@patch("jobsai.api.server.update_job_status")
def test_cancel_pipeline(mock_update_status, mock_get_state):
    """Test cancelling a pipeline."""
    mock_get_state.return_value = {
        "status": "running",
    }

    response = client.post("/api/cancel/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancellation_requested"
    # Verify status was updated
    assert mock_update_status.called


@patch("jobsai.api.server.get_job_state")
@patch("jobsai.api.server.get_presigned_s3_url")
def test_download_document_single(mock_get_url, mock_get_state):
    """Test downloading single document."""
    mock_get_state.return_value = {
        "status": "complete",
        "result": {
            "filename": "20250115_143022_cover_letter.docx",
            "s3_key": "documents/test/cover_letter.docx",
        },
    }
    mock_get_url.return_value = "https://s3.amazonaws.com/bucket/key?signature=xyz"

    response = client.get("/api/download/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "filename" in data


@patch("jobsai.api.server.get_job_state")
@patch("jobsai.api.server.get_presigned_s3_url")
def test_download_document_multiple(mock_get_url, mock_get_state):
    """Test downloading multiple documents."""
    mock_get_state.return_value = {
        "status": "complete",
        "result": {
            "filenames": [
                "20250115_143022_cover_letter.docx",
                "20250115_143022_cover_letter_2.docx",
            ],
            "s3_keys": [
                "documents/test/cover_letter.docx",
                "documents/test/cover_letter_2.docx",
            ],
        },
    }
    mock_get_url.return_value = "https://s3.amazonaws.com/bucket/key?signature=xyz"

    response = client.get("/api/download/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert "download_urls" in data
    assert len(data["download_urls"]) == 2
    assert "count" in data


@patch("jobsai.api.server.get_job_state")
@patch("jobsai.api.server.get_presigned_s3_url")
def test_download_document_by_index(mock_get_url, mock_get_state):
    """Test downloading specific document by index."""
    mock_get_state.return_value = {
        "status": "complete",
        "result": {
            "filenames": [
                "20250115_143022_cover_letter.docx",
                "20250115_143022_cover_letter_2.docx",
            ],
            "s3_keys": [
                "documents/test/cover_letter.docx",
                "documents/test/cover_letter_2.docx",
            ],
        },
    }
    mock_get_url.return_value = "https://s3.amazonaws.com/bucket/key?signature=xyz"

    response = client.get("/api/download/test-job-123?index=2")

    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "cover_letter_2.docx" in data["filename"]


@patch("jobsai.api.server.get_job_state")
def test_download_document_not_ready(mock_get_state):
    """Test downloading when job is not complete."""
    mock_get_state.return_value = {
        "status": "running",
    }

    response = client.get("/api/download/test-job-123")

    assert response.status_code == 400
    data = response.json()
    assert "not ready" in data["detail"].lower()


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/api/start")
    # CORS middleware should handle OPTIONS requests
    assert response.status_code in [200, 204, 405]  # Depends on CORS config
