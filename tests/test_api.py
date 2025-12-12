"""API tests for tokopedia-scraper."""

import pytest
from api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "tokopedia-scraper"
        assert "version" in data


class TestJobsEndpoint:
    """Tests for the jobs endpoints."""

    def test_create_job_missing_query(self, client):
        """Test that creating a job without query fails."""
        response = client.post("/api/v1/jobs")
        assert response.status_code == 422  # Missing required parameter

    def test_create_job_with_query(self, client):
        """Test creating a job with valid query."""
        response = client.post("/api/v1/jobs?query=smartphone")
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "smartphone" in data["message"]

    def test_create_job_with_all_params(self, client):
        """Test creating a job with all parameters."""
        response = client.post(
            "/api/v1/jobs?query=smartphone&brand=iPhone&max_products=50&pages=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_create_job_invalid_max_products(self, client):
        """Test that invalid max_products is rejected."""
        response = client.post("/api/v1/jobs?query=smartphone&max_products=0")
        assert response.status_code == 422  # Validation error

    def test_create_job_invalid_pages(self, client):
        """Test that invalid pages is rejected."""
        response = client.post("/api/v1/jobs?query=smartphone&pages=100")
        assert response.status_code == 422  # Validation error (max 50)

    def test_get_nonexistent_job(self, client):
        """Test that getting a nonexistent job returns 404."""
        response = client.get("/api/v1/jobs/nonexistent-job-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_results_nonexistent_job(self, client):
        """Test that getting results for nonexistent job returns 404."""
        response = client.get("/api/v1/jobs/nonexistent-job-id/results")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_list_jobs(self, client):
        """Test listing jobs."""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "jobs" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_jobs_with_status_filter(self, client):
        """Test listing jobs with status filter."""
        response = client.get("/api/v1/jobs?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data

    def test_list_jobs_pagination(self, client):
        """Test listing jobs with pagination."""
        response = client.get("/api/v1/jobs?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_delete_nonexistent_job(self, client):
        """Test that deleting a nonexistent job returns 404."""
        response = client.delete("/api/v1/jobs/nonexistent-job-id")
        assert response.status_code == 404


class TestJobResults:
    """Tests for job results endpoints."""

    def test_results_pagination_params(self, client):
        """Test that results endpoint accepts pagination params."""
        # This will return 404 since job doesn't exist, but validates param handling
        response = client.get("/api/v1/jobs/test-job-id/results?page=2&page_size=50")
        assert response.status_code == 404  # Job doesn't exist

    def test_results_invalid_page(self, client):
        """Test that invalid page parameter is rejected."""
        response = client.get("/api/v1/jobs/test-job-id/results?page=0")
        assert response.status_code == 422  # Validation error

    def test_results_invalid_page_size(self, client):
        """Test that invalid page_size parameter is rejected."""
        response = client.get("/api/v1/jobs/test-job-id/results?page_size=10000")
        assert response.status_code == 422  # Validation error (max 1000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
