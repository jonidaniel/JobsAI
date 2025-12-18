"""
API Integration Tests.

Tests the complete API flow from request to response, including:
- Request validation
- State management
- Lambda invocation
- Progress tracking
- Download URL generation
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from jobsai.api.server import app
from jobsai.config.schemas import FrontendPayload

client = TestClient(app)


@pytest.fixture
def mock_lambda_invoke():
    """Mock Lambda invocation."""
    with patch("jobsai.api.handlers.lambda_invocation.invoke_worker_lambda") as mock:
        yield mock


@pytest.fixture
def mock_state_manager():
    """Mock state manager functions."""
    with (
        patch("jobsai.api.routes.pipeline.store_job_state") as mock_store,
        patch("jobsai.api.routes.pipeline.get_job_state") as mock_get,
        patch("jobsai.api.routes.pipeline.update_job_status") as mock_update,
    ):
        yield {
            "store": mock_store,
            "get": mock_get,
            "update": mock_update,
        }


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def test_complete_start_progress_download_flow(
        self, mock_lambda_invoke, mock_state_manager
    ):
        """Test complete flow: start → progress → download."""
        # Step 1: Start pipeline
        payload = {
            "general": [
                {"job-level": ["Expert"]},
                {"job-boards": ["Duunitori"]},
                {"deep-mode": "Yes"},
                {"cover-letter-num": 1},
                {"cover-letter-style": ["Professional"]},
            ],
            "languages": [{"python": 5}],
            "additional-info": [{"additional-info": "Test"}],
        }

        response = client.post("/api/start", json=payload)
        assert response.status_code == 200
        assert "job_id" in response.json()

        job_id = response.json()["job_id"]

        # Verify state was stored
        mock_state_manager["store"].assert_called_once()
        mock_lambda_invoke.assert_called_once()

        # Step 2: Check progress (running)
        mock_state_manager["get"].return_value = {
            "status": "running",
            "progress": {"phase": "profiling", "message": "Creating your profile..."},
        }

        response = client.get(f"/api/progress/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "progress" in data
        assert data["progress"]["phase"] == "profiling"

        # Step 3: Check progress (complete)
        mock_state_manager["get"].return_value = {
            "status": "complete",
            "result": {
                "filename": "20250115_143022_cover_letter.docx",
                "s3_key": "documents/test-job-id/20250115_143022_cover_letter.docx",
            },
        }

        response = client.get(f"/api/progress/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert "filename" in data

        # Step 4: Get download URL
        with patch("jobsai.api.routes.download.get_presigned_s3_url") as mock_presigned:
            mock_presigned.return_value = "https://s3.amazonaws.com/presigned-url"

            response = client.get(f"/api/download/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["filename"] == "20250115_143022_cover_letter.docx"

    def test_multiple_documents_download_flow(
        self, mock_lambda_invoke, mock_state_manager
    ):
        """Test download flow with multiple documents."""
        payload = {
            "general": [
                {"job-level": ["Expert"]},
                {"job-boards": ["Duunitori"]},
                {"deep-mode": "Yes"},
                {"cover-letter-num": 3},
                {"cover-letter-style": ["Professional"]},
            ],
            "languages": [{"python": 5}],
            "additional-info": [{"additional-info": "Test"}],
        }

        response = client.post("/api/start", json=payload)
        job_id = response.json()["job_id"]

        # Set state to complete with multiple documents
        mock_state_manager["get"].return_value = {
            "status": "complete",
            "result": {
                "filenames": [
                    "20250115_143022_cover_letter.docx",
                    "20250115_143022_cover_letter_2.docx",
                    "20250115_143022_cover_letter_3.docx",
                ],
                "s3_keys": [
                    "documents/test-job-id/20250115_143022_cover_letter.docx",
                    "documents/test-job-id/20250115_143022_cover_letter_2.docx",
                    "documents/test-job-id/20250115_143022_cover_letter_3.docx",
                ],
                "count": 3,
            },
        }

        # Get all download URLs
        with patch("jobsai.api.routes.download.get_presigned_s3_url") as mock_presigned:
            mock_presigned.side_effect = [
                "https://s3.amazonaws.com/url1",
                "https://s3.amazonaws.com/url2",
                "https://s3.amazonaws.com/url3",
            ]

            response = client.get(f"/api/download/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert "download_urls" in data
            assert len(data["download_urls"]) == 3
            assert data["count"] == 3

            # Get specific document by index
            response = client.get(f"/api/download/{job_id}?index=2")
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["filename"] == "20250115_143022_cover_letter_2.docx"

    def test_cancellation_flow(self, mock_lambda_invoke, mock_state_manager):
        """Test pipeline cancellation flow."""
        payload = {
            "general": [
                {"job-level": ["Expert"]},
                {"job-boards": ["Duunitori"]},
                {"deep-mode": "Yes"},
                {"cover-letter-num": 1},
                {"cover-letter-style": ["Professional"]},
            ],
            "languages": [{"python": 5}],
            "additional-info": [{"additional-info": "Test"}],
        }

        response = client.post("/api/start", json=payload)
        job_id = response.json()["job_id"]

        # Set state to running
        mock_state_manager["get"].return_value = {
            "status": "running",
            "progress": {"phase": "profiling"},
        }

        # Cancel pipeline
        response = client.post(f"/api/cancel/{job_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancellation_requested"

        # Verify status was updated
        mock_state_manager["update"].assert_called_once_with(job_id, "cancelling")

    def test_error_handling_flow(self, mock_lambda_invoke, mock_state_manager):
        """Test error handling in API flow."""
        payload = {
            "general": [
                {"job-level": ["Expert"]},
                {"job-boards": ["Duunitori"]},
                {"deep-mode": "Yes"},
                {"cover-letter-num": 1},
                {"cover-letter-style": ["Professional"]},
            ],
            "languages": [{"python": 5}],
            "additional-info": [{"additional-info": "Test"}],
        }

        # Simulate Lambda invocation failure
        mock_lambda_invoke.side_effect = Exception("Lambda invocation failed")

        response = client.post("/api/start", json=payload)
        assert response.status_code == 500

        # Verify error state was set
        mock_state_manager["update"].assert_called_once()
        call_args = mock_state_manager["update"].call_args
        assert call_args[0][1] == "error"  # status is "error"

    def test_validation_error_handling(self):
        """Test request validation error handling."""
        # Invalid payload (missing required fields)
        invalid_payload = {
            "general": [{"job-level": ["Expert"]}],  # Missing other required fields
        }

        response = client.post("/api/start", json=invalid_payload)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "message" in response.json()

    def test_progress_not_found(self, mock_state_manager):
        """Test progress endpoint when job not found."""
        mock_state_manager["get"].return_value = None

        response = client.get("/api/progress/non-existent-job-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_download_not_ready(self, mock_state_manager):
        """Test download endpoint when job not complete."""
        mock_state_manager["get"].return_value = {
            "status": "running",
            "progress": {"phase": "profiling"},
        }

        response = client.get("/api/download/test-job-id")
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()
