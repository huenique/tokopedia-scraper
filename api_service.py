#!/usr/bin/env python3
"""
Tokopedia Scraper REST API Service
=================================

REST-conforming HTTP API service for Tokopedia product scraping.
Provides standardized endpoints that can be used across different scraper implementations.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Import the main scraper functionality
from tokopedia_graphql import TokopediaGraphQLScraper


class JobStatus(str, Enum):
    """Enumeration of possible job statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeRequest(BaseModel):
    """Request model for scrape operations."""

    query: str = Field(..., description="Search query/keyword")
    brand: str | None = Field(None, description="Brand filter")
    max_products: int = Field(
        100, ge=1, le=1000, description="Maximum products to scrape"
    )
    pages: int | None = Field(
        None, ge=1, le=50, description="Number of pages to scrape"
    )
    output_format: str = Field(
        "json", pattern="^(json|csv)$", description="Output format"
    )

    class Config:
        json_schema_extra: dict[str, Any] = {
            "example": {
                "query": "smartphone",
                "brand": "iPhone",
                "max_products": 100,
                "pages": 3,
                "output_format": "json",
            }
        }


class JobInfo(BaseModel):
    """Job information model."""

    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    request_params: ScrapeRequest
    progress: str | None = None
    error_message: str | None = None
    result_count: int | None = None


class ScrapeResponse(BaseModel):
    """Response model for scrape operations."""

    job_id: str
    status: JobStatus
    message: str


class JobManager:
    """Manages scraping jobs and their statuses."""

    def __init__(self):
        self.jobs: dict[str, JobInfo] = {}
        self.results: dict[str, list[dict[str, Any]]] = {}
        self.active_tasks: dict[str, asyncio.Task[None]] = {}

    def create_job(self, request: ScrapeRequest) -> str:
        """Create a new scraping job."""
        job_id = str(uuid.uuid4())
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            request_params=request,
        )
        self.jobs[job_id] = job_info
        return job_id

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: str | None = None,
        error_message: str | None = None,
        result_count: int | None = None,
    ):
        """Update job status and metadata."""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            self.jobs[job_id].updated_at = datetime.now()
            if progress:
                self.jobs[job_id].progress = progress
            if error_message:
                self.jobs[job_id].error_message = error_message
            if result_count is not None:
                self.jobs[job_id].result_count = result_count

    def get_job(self, job_id: str) -> JobInfo | None:
        """Get job information."""
        return self.jobs.get(job_id)

    def set_results(self, job_id: str, results: list[dict[str, Any]]) -> None:
        """Set job results."""
        self.results[job_id] = results

    def get_results(self, job_id: str) -> list[dict[str, Any]] | None:
        """Get job results."""
        return self.results.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its results."""
        deleted = False
        if job_id in self.jobs:
            # Cancel task if it's still running
            if job_id in self.active_tasks:
                self.active_tasks[job_id].cancel()
                del self.active_tasks[job_id]
            del self.jobs[job_id]
            deleted = True
        if job_id in self.results:
            del self.results[job_id]
        return deleted


# Global job manager instance
job_manager = JobManager()

# FastAPI app instance
app = FastAPI(
    title="Tokopedia Scraper API",
    description="REST API for Tokopedia product scraping",
    version="1.0.0",
)


async def execute_scraping_job(job_id: str, request: ScrapeRequest) -> None:
    """Execute the actual scraping job."""
    try:
        job_manager.update_job_status(
            job_id, JobStatus.RUNNING, "Initializing scraper..."
        )

        # Create Tokopedia scraper instance
        config: dict[str, Any] = {
            "keyword": request.query,
            "brand": request.brand,
            "max_products": request.max_products,
            "max_pages": request.pages,
        }
        scraper = TokopediaGraphQLScraper(config)

        job_manager.update_job_status(job_id, JobStatus.RUNNING, "Scraping products...")

        # Execute the scraping (GraphQL version for better performance)
        results = scraper.scrape_products()

        job_manager.set_results(job_id, results)
        job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            "Scraping completed successfully",
            result_count=len(results),
        )

    except asyncio.CancelledError:
        job_manager.update_job_status(job_id, JobStatus.CANCELLED, "Job was cancelled")
    except Exception as e:
        job_manager.update_job_status(
            job_id, JobStatus.FAILED, error_message=f"Scraping failed: {str(e)}"
        )
    finally:
        # Remove from active tasks
        if job_id in job_manager.active_tasks:
            del job_manager.active_tasks[job_id]


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/scrape/search", response_model=ScrapeResponse)
async def start_scrape_job(request: ScrapeRequest):
    """Start a new scraping job."""
    job_id = job_manager.create_job(request)

    # Create and store the task
    task = asyncio.create_task(execute_scraping_job(job_id, request))
    job_manager.active_tasks[job_id] = task

    return ScrapeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Scraping job started successfully",
    )


@app.get("/scrape/status/{job_id}", response_model=JobInfo)
async def get_job_status(job_id: str) -> JobInfo:
    """Get the status of a scraping job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/scrape/results/{job_id}")
async def get_job_results(job_id: str) -> dict[str, Any]:
    """Get the results of a completed scraping job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job.status}",
        )

    results = job_manager.get_results(job_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Results not found")

    return {
        "job_id": job_id,
        "status": job.status,
        "result_count": len(results),
        "results": results,
    }


@app.get("/scrape/jobs")
async def list_jobs() -> dict[str, list[dict[str, Any]]]:
    """List all scraping jobs."""
    jobs: list[dict[str, Any]] = [
        {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "result_count": job.result_count,
        }
        for job in job_manager.jobs.values()
    ]
    return {"jobs": jobs}


@app.delete("/scrape/jobs/{job_id}")
async def delete_job(job_id: str) -> dict[str, str]:
    """Cancel or delete a scraping job."""
    if not job_manager.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": f"Job {job_id} deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(
        "api_service:app", host="0.0.0.0", port=8002, reload=True, log_level="info"
    )
