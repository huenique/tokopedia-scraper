#!/usr/bin/env python3
"""
Regenerate CSV files for existing job results.

This script processes all existing job results and creates CSV files
for jobs that only have JSON results.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from csv_writer import TokopediaCSVWriter


def regenerate_csv_for_job(job_dir: Path) -> bool:
    """
    Regenerate CSV for a single job.

    Args:
        job_dir: Path to the job directory

    Returns:
        True if CSV was generated successfully
    """
    json_file = job_dir / "json" / "results.json"
    csv_file = job_dir / "csv" / "results.csv"

    # Check if JSON file exists
    if not json_file.exists():
        print(f"⏭️  Skipping {job_dir.name} - no JSON file")
        return False

    # Check if CSV already exists
    if csv_file.exists():
        print(f"⏭️  Skipping {job_dir.name} - CSV already exists")
        return False

    try:
        # Load JSON results
        with open(json_file, "r") as f:
            results = json.load(f)

        if not results:
            print(f"⚠️  Skipping {job_dir.name} - empty results")
            return False

        # Create CSV
        csv_writer = TokopediaCSVWriter(csv_file)
        count = csv_writer.write_products(results)

        print(f"✅ Generated CSV for {job_dir.name} ({count} products)")
        return True

    except Exception as e:
        print(f"❌ Error processing {job_dir.name}: {e}")
        return False


def main():
    """Main function to regenerate all CSV files."""
    results_dir = Path(__file__).parent / "results" / "jobs"

    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return

    # Find all job directories
    job_dirs = [d for d in results_dir.iterdir() if d.is_dir()]

    if not job_dirs:
        print("No job directories found")
        return

    print(f"Found {len(job_dirs)} job directories")
    print("=" * 60)

    success_count = 0
    for job_dir in sorted(job_dirs):
        if regenerate_csv_for_job(job_dir):
            success_count += 1

    print("=" * 60)
    print(f"✅ Successfully generated {success_count} CSV files")


if __name__ == "__main__":
    main()
