"""Configuration management for tokopedia-scraper."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for the Tokopedia Scraper."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    results_dir: Path = field(default_factory=lambda: Path("results"))

    # Scraping settings
    default_max_products: int = 100
    default_pages: int = 5
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        base_dir = Path(__file__).parent.parent
        results_dir = base_dir / "results"

        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            base_dir=base_dir,
            results_dir=results_dir,
            default_max_products=int(os.getenv("DEFAULT_MAX_PRODUCTS", "100")),
            default_pages=int(os.getenv("DEFAULT_PAGES", "5")),
            timeout=int(os.getenv("TIMEOUT", "30")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "base_dir": str(self.base_dir),
            "results_dir": str(self.results_dir),
            "default_max_products": self.default_max_products,
            "default_pages": self.default_pages,
            "timeout": self.timeout,
        }
