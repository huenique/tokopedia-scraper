"""Path utilities for tokopedia-scraper."""

from pathlib import Path
from typing import Optional


class PathUtils:
    """Utility class for managing scraper paths."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize path utilities.

        Args:
            base_dir: Base directory for the scraper. Defaults to scraper root.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = base_dir

        self.results_dir = self.base_dir / "results"

    def get_job_dir(self, job_id: str) -> Path:
        """Get the directory for a specific job.

        Args:
            job_id: The job identifier.

        Returns:
            Path to the job directory.
        """
        return self.results_dir / "jobs" / job_id

    def get_job_csv_dir(self, job_id: str) -> Path:
        """Get the CSV output directory for a job.

        Args:
            job_id: The job identifier.

        Returns:
            Path to the job's CSV directory.
        """
        return self.get_job_dir(job_id) / "csv"

    def get_job_json_dir(self, job_id: str) -> Path:
        """Get the JSON output directory for a job.

        Args:
            job_id: The job identifier.

        Returns:
            Path to the job's JSON directory.
        """
        return self.get_job_dir(job_id) / "json"

    def ensure_job_dirs(self, job_id: str) -> dict[str, Path]:
        """Ensure all job directories exist.

        Args:
            job_id: The job identifier.

        Returns:
            Dictionary with paths to job directories.
        """
        dirs = {
            "job": self.get_job_dir(job_id),
            "csv": self.get_job_csv_dir(job_id),
            "json": self.get_job_json_dir(job_id),
        }

        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)

        return dirs

    def get_job_metadata_path(self, job_id: str) -> Path:
        """Get the path to a job's metadata file.

        Args:
            job_id: The job identifier.

        Returns:
            Path to the job metadata JSON file.
        """
        return self.get_job_dir(job_id) / "job_metadata.json"

    def list_jobs(self) -> list[str]:
        """List all job IDs.

        Returns:
            List of job IDs.
        """
        jobs_dir = self.results_dir / "jobs"
        if not jobs_dir.exists():
            return []

        return [d.name for d in jobs_dir.iterdir() if d.is_dir()]
