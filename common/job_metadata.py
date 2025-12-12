"""Job metadata management for tokopedia-scraper."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


class JobStatus(str, Enum):
    """Status of a scraping job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobMetadata:
    """Metadata for a scraping job."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    results_summary: dict[str, Any] = field(default_factory=dict)
    output_files: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, job_id: Optional[str] = None, **parameters: Any) -> "JobMetadata":
        """Create a new job metadata instance.

        Args:
            job_id: Optional job ID. Auto-generated if not provided.
            **parameters: Job parameters to store.

        Returns:
            New JobMetadata instance.
        """
        return cls(
            job_id=job_id or str(uuid4()),
            parameters=parameters,
        )

    @classmethod
    def load(cls, path: Path) -> "JobMetadata":
        """Load job metadata from a file.

        Args:
            path: Path to the metadata JSON file.

        Returns:
            JobMetadata instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If the file is invalid JSON.
        """
        with open(path, "r") as f:
            data = json.load(f)

        # Convert status string back to enum
        if isinstance(data.get("status"), str):
            data["status"] = JobStatus(data["status"])

        return cls(**data)

    def save(self, path: Path) -> None:
        """Save job metadata to a file.

        Args:
            path: Path to save the metadata JSON file.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        # Convert enum to string for JSON serialization
        data["status"] = self.status.value

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def update_status(self, status: JobStatus, error_message: Optional[str] = None) -> None:
        """Update job status.

        Args:
            status: New status.
            error_message: Optional error message (for failed status).
        """
        self.status = status
        self.updated_at = datetime.utcnow().isoformat()

        if status == JobStatus.RUNNING and self.started_at is None:
            self.started_at = self.updated_at

        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            self.completed_at = self.updated_at

        if error_message:
            self.error_message = error_message

    def add_output_file(self, file_path: str) -> None:
        """Add an output file to the job.

        Args:
            file_path: Path to the output file (relative to job directory).
        """
        if file_path not in self.output_files:
            self.output_files.append(file_path)
            self.updated_at = datetime.utcnow().isoformat()

    def set_results_summary(self, **summary: Any) -> None:
        """Set the results summary.

        Args:
            **summary: Summary key-value pairs.
        """
        self.results_summary.update(summary)
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the job metadata.
        """
        data = asdict(self)
        data["status"] = self.status.value
        return data
