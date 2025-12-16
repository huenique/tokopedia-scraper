"""FastAPI application for tokopedia-scraper.

Provides REST API endpoints for managing Tokopedia scraping jobs.
Aligned with /api/v1/jobs pattern used across all scrapers.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from common.config import Config
from common.job_metadata import JobMetadata, JobStatus
from common.logger import get_logger
from common.path_utils import PathUtils
from csv_writer import TokopediaCSVWriter
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# Import the scraper and CSV writer
from tokopedia_graphql import TokopediaGraphQLScraper

logger = get_logger(__name__)


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    results_summary: dict[str, Any] = Field(default_factory=dict)
    output_files: list[str] = Field(default_factory=list)


class JobResultsResponse(BaseModel):
    """Response model for job results."""

    job_id: str
    status: str
    total_items: int
    page: int
    page_size: int
    total_pages: int
    items: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    service: str
    version: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config.from_env()
    path_utils = PathUtils(config.base_dir)

    app = FastAPI(
        title="Tokopedia Scraper API",
        description="API for scraping Tokopedia product information",
        version="1.0.0",
    )

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            service="tokopedia-scraper",
            version="1.0.0",
        )

    @app.post("/api/v1/jobs", response_model=JobResponse, tags=["Jobs"])
    async def create_job(
        background_tasks: BackgroundTasks,
        query: str = Query(..., description="Search query/keyword"),
        brand: Optional[str] = Query(default=None, description="Brand filter"),
        max_products: int = Query(default=100, ge=1, le=1000, description="Max products to scrape"),
        pages: Optional[int] = Query(default=None, ge=1, le=50, description="Number of pages"),
    ) -> JobResponse:
        """Create a new scraping job."""
        job_id = str(uuid4())

        # Create job metadata
        job_metadata = JobMetadata.create(
            job_id=job_id,
            query=query,
            brand=brand,
            max_products=max_products,
            pages=pages,
        )

        # Ensure job directories exist
        path_utils.ensure_job_dirs(job_id)
        job_metadata.save(path_utils.get_job_metadata_path(job_id))

        # Run the job in the background
        background_tasks.add_task(
            run_scraper_job,
            job_metadata,
            path_utils,
            query,
            brand,
            max_products,
            pages,
        )

        return JobResponse(
            job_id=job_id,
            status=job_metadata.status.value,
            message=f"Scraping job started for query: {query}",
        )

    @app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
    async def get_job_status(job_id: str) -> JobStatusResponse:
        """Get the status of a job."""
        metadata_path = path_utils.get_job_metadata_path(job_id)

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job_metadata = JobMetadata.load(metadata_path)

        return JobStatusResponse(**job_metadata.to_dict())

    @app.get("/api/v1/jobs/{job_id}/results", response_model=JobResultsResponse, tags=["Jobs"])
    async def get_job_results(
        job_id: str,
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=100, ge=1, le=1000, description="Items per page"),
    ) -> JobResultsResponse:
        """Get paginated results for a job."""
        metadata_path = path_utils.get_job_metadata_path(job_id)

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job_metadata = JobMetadata.load(metadata_path)

        # Load results from JSON files
        json_dir = path_utils.get_job_json_dir(job_id)
        all_items: list[dict[str, Any]] = []

        if json_dir.exists():
            for json_file in json_dir.glob("*.json"):
                if json_file.name != "job_metadata.json":
                    try:
                        with open(json_file, "r") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                all_items.extend(data)
                            elif isinstance(data, dict):
                                all_items.append(data)
                    except Exception as e:
                        logger.warning(f"Error reading {json_file}: {e}")

        # Paginate results
        total_items = len(all_items)
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = all_items[start_idx:end_idx]

        return JobResultsResponse(
            job_id=job_id,
            status=job_metadata.status.value,
            total_items=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items,
        )

    @app.get("/api/v1/jobs", tags=["Jobs"])
    async def list_jobs(
        status: Optional[str] = Query(default=None, description="Filter by status"),
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> dict[str, Any]:
        """List all jobs with optional status filter."""
        job_ids = path_utils.list_jobs()
        jobs: list[dict[str, Any]] = []

        for job_id in job_ids:
            try:
                metadata_path = path_utils.get_job_metadata_path(job_id)
                if metadata_path.exists():
                    job_metadata = JobMetadata.load(metadata_path)
                    if status is None or job_metadata.status.value == status:
                        jobs.append(job_metadata.to_dict())
            except Exception as e:
                logger.warning(f"Error loading job {job_id}: {e}")

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Paginate
        total_jobs = len(jobs)
        total_pages = max(1, (total_jobs + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return {
            "total_jobs": total_jobs,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "jobs": jobs[start_idx:end_idx],
        }

    @app.delete("/api/v1/jobs/{job_id}", tags=["Jobs"])
    async def delete_job(job_id: str) -> dict[str, str]:
        """Delete a job and its files."""
        job_dir = path_utils.get_job_dir(job_id)

        if not job_dir.exists():
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        import shutil
        shutil.rmtree(job_dir)

        return {"message": f"Job {job_id} deleted successfully"}

    return app


async def run_scraper_job(
    job_metadata: JobMetadata,
    path_utils: PathUtils,
    query: str,
    brand: Optional[str],
    max_products: int,
    pages: Optional[int],
) -> None:
    """Run a scraper job in the background."""
    try:
        job_metadata.update_status(JobStatus.RUNNING)
        job_metadata.save(path_utils.get_job_metadata_path(job_metadata.job_id))

        # Create scraper instance with config
        config = {
            "keyword": query,
            "brand": brand,
            "max_products": max_products,
            "max_pages": pages,
            "delay": 1.0,
        }
        scraper = TokopediaGraphQLScraper(config)

        logger.info(f"Starting scrape for query: {query}")

        # Execute the scraping (synchronous method)
        results = scraper.scrape_products()

        # Save JSON results
        json_dir = path_utils.get_job_json_dir(job_metadata.job_id)
        results_file = json_dir / "results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        job_metadata.add_output_file("json/results.json")

        # Save CSV results
        csv_dir = path_utils.get_job_csv_dir(job_metadata.job_id)
        csv_file = csv_dir / "results.csv"
        csv_writer = TokopediaCSVWriter(csv_file)
        csv_writer.write_products(results)
        job_metadata.add_output_file("csv/results.csv")

        logger.info(f"Saved {len(results)} products to JSON and CSV")

        job_metadata.set_results_summary(
            total_products=len(results),
            query=query,
            brand=brand,
            max_products=max_products,
            pages=pages,
        )
        job_metadata.update_status(JobStatus.COMPLETED)
        logger.info(f"Job {job_metadata.job_id} completed with {len(results)} results")

    except asyncio.CancelledError:
        job_metadata.update_status(JobStatus.CANCELLED, error_message="Job was cancelled")
        logger.info(f"Job {job_metadata.job_id} was cancelled")

    except Exception as e:
        job_metadata.update_status(JobStatus.FAILED, error_message=str(e))
        logger.exception(f"Job {job_metadata.job_id} failed")

    finally:
        job_metadata.save(path_utils.get_job_metadata_path(job_metadata.job_id))


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = Config.from_env()
    uvicorn.run(app, host=config.host, port=config.port)
