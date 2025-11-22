#!/usr/bin/env python3
"""
CLI tool for batch importing disc images.

Usage:
    From the backend directory:
        python batch_import_discs.py /path/to/images/directory

    Or as a module:
        python -m app.disc_identification.cli.batch_import /path/to/images/directory

This tool will:
- Process all images in the specified directory
- Display progress every 100 images
- Log successes and failures
- Generate a process report text file
"""
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from ..disc_registration_service import (
    DiscRegistrationService,
    DiscRegistrationResult
)
from ..config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchImportStats:
    """Statistics for batch import operation."""

    def __init__(self):
        self.total_files = 0
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None

    def start(self):
        """Mark start of processing."""
        self.start_time = datetime.now()

    def finish(self):
        """Mark end of processing."""
        self.end_time = datetime.now()

    def get_duration(self) -> float:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def increment_processed(self):
        """Increment processed counter."""
        self.processed += 1

    def increment_successful(self):
        """Increment successful counter."""
        self.successful += 1

    def increment_failed(self):
        """Increment failed counter."""
        self.failed += 1

    def increment_skipped(self):
        """Increment skipped counter."""
        self.skipped += 1


class ProcessReport:
    """Process report for batch import."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.successful_images: List[Tuple[str, int]] = []  # (filename, disc_id)
        self.failed_images: List[Tuple[str, str]] = []  # (filename, error_message)

    def add_success(self, filename: str, disc_id: int):
        """Add successful import."""
        self.successful_images.append((filename, disc_id))

    def add_failure(self, filename: str, error_message: str):
        """Add failed import."""
        self.failed_images.append((filename, error_message))

    def save_to_file(self, stats: BatchImportStats) -> Path:
        """
        Save report to text file.

        Args:
            stats: BatchImportStats with processing statistics

        Returns:
            Path to saved report file
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"process-report-{timestamp}.txt"
        report_path = self.directory / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("DISC BATCH IMPORT REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Summary
            f.write(f"Directory: {self.directory}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Duration: {stats.get_duration():.2f} seconds\n\n")

            f.write(f"Total files found: {stats.total_files}\n")
            f.write(f"Files processed: {stats.processed}\n")
            f.write(f"Successful imports: {stats.successful}\n")
            f.write(f"Failed imports: {stats.failed}\n")
            f.write(f"Skipped files: {stats.skipped}\n\n")

            # Successful imports
            f.write("=" * 80 + "\n")
            f.write("SUCCESSFUL IMPORTS\n")
            f.write("=" * 80 + "\n\n")

            if self.successful_images:
                for filename, disc_id in self.successful_images:
                    f.write(f"[SUCCESS] {filename} -> Disc ID: {disc_id}\n")
            else:
                f.write("No successful imports.\n")

            f.write("\n")

            # Failed imports
            f.write("=" * 80 + "\n")
            f.write("FAILED IMPORTS\n")
            f.write("=" * 80 + "\n\n")

            if self.failed_images:
                for filename, error_msg in self.failed_images:
                    f.write(f"[FAILED] {filename}\n")
                    f.write(f"  Error: {error_msg}\n\n")
            else:
                f.write("No failed imports.\n")

        logger.info(f"Process report saved to: {report_path}")
        return report_path


def get_image_files(directory: Path) -> List[Path]:
    """
    Get all image files from directory.

    Args:
        directory: Directory to scan

    Returns:
        List of image file paths
    """
    image_files = []
    for ext in Config.ALLOWED_EXTENSIONS:
        # Case-insensitive search
        image_files.extend(directory.glob(f"*{ext}"))
        image_files.extend(directory.glob(f"*{ext.upper()}"))

    # Remove duplicates and sort
    image_files = sorted(set(image_files))

    return image_files


def print_progress(stats: BatchImportStats):
    """
    Print progress report.

    Args:
        stats: Current statistics
    """
    print(f"\nProgress: {stats.processed}/{stats.total_files} images processed")
    print(f"  Successful: {stats.successful}")
    print(f"  Failed: {stats.failed}")
    print(f"  Skipped: {stats.skipped}")


def batch_import_images(
    directory: Path,
    progress_interval: int = 100,
    owner_name: str = "Batch Import",
    owner_contact: str = "batch@example.com"
) -> Tuple[BatchImportStats, ProcessReport]:
    """
    Batch import images from directory.

    Args:
        directory: Directory containing images
        progress_interval: Print progress every N images
        owner_name: Default owner name for discs
        owner_contact: Default owner contact for discs

    Returns:
        Tuple of (statistics, process_report)
    """
    # Initialize
    stats = BatchImportStats()
    report = ProcessReport(directory)
    service = DiscRegistrationService()

    # Get all image files
    image_files = get_image_files(directory)
    stats.total_files = len(image_files)

    print(f"\n{'=' * 80}")
    print(f"BATCH IMPORT STARTED")
    print(f"{'=' * 80}")
    print(f"Directory: {directory}")
    print(f"Total images found: {stats.total_files}")
    print(f"Progress will be reported every {progress_interval} images")
    print(f"{'=' * 80}\n")

    if stats.total_files == 0:
        print("No image files found in directory.")
        return stats, report

    # Start processing
    stats.start()

    for idx, image_path in enumerate(image_files, start=1):
        try:
            # Register image
            result = service.register_from_file(
                image_path=image_path,
                owner_name=owner_name,
                owner_contact=owner_contact,
                status='registered',
                upload_status='SUCCESS'
            )

            stats.increment_processed()

            if result.success:
                stats.increment_successful()
                report.add_success(image_path.name, result.disc_id)
                logger.info(f"[{idx}/{stats.total_files}] SUCCESS: {image_path.name} -> Disc ID {result.disc_id}")
            else:
                stats.increment_failed()
                report.add_failure(image_path.name, result.error_message or "Unknown error")
                logger.warning(f"[{idx}/{stats.total_files}] FAILED: {image_path.name} - {result.error_message}")

        except Exception as e:
            stats.increment_processed()
            stats.increment_failed()
            error_msg = f"Unexpected error: {str(e)}"
            report.add_failure(image_path.name, error_msg)
            logger.error(f"[{idx}/{stats.total_files}] ERROR: {image_path.name} - {error_msg}")

        # Print progress at intervals
        if idx % progress_interval == 0 or idx == stats.total_files:
            print_progress(stats)

    # Finish
    stats.finish()

    # Print final summary
    print(f"\n{'=' * 80}")
    print(f"BATCH IMPORT COMPLETED")
    print(f"{'=' * 80}")
    print(f"Total files: {stats.total_files}")
    print(f"Processed: {stats.processed}")
    print(f"Successful: {stats.successful}")
    print(f"Failed: {stats.failed}")
    print(f"Skipped: {stats.skipped}")
    print(f"Duration: {stats.get_duration():.2f} seconds")
    print(f"{'=' * 80}\n")

    return stats, report


def main():
    """Main entry point for CLI tool."""
    parser = argparse.ArgumentParser(
        description='Batch import disc images from a directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all images from a directory
  python batch_import.py /path/to/images

  # Import with custom owner information
  python batch_import.py /path/to/images --owner "John Doe" --contact "john@example.com"

  # Change progress reporting interval
  python batch_import.py /path/to/images --progress-interval 50
        """
    )

    parser.add_argument(
        'directory',
        type=str,
        help='Directory containing images to import'
    )

    parser.add_argument(
        '--owner',
        type=str,
        default='Batch Import',
        help='Default owner name for imported discs (default: "Batch Import")'
    )

    parser.add_argument(
        '--contact',
        type=str,
        default='batch@example.com',
        help='Default owner contact for imported discs (default: "batch@example.com")'
    )

    parser.add_argument(
        '--progress-interval',
        type=int,
        default=100,
        help='Print progress every N images (default: 100)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}")
        sys.exit(1)

    # Validate configuration
    try:
        Config.validate()
    except Exception as e:
        print(f"Error: Invalid configuration: {e}")
        sys.exit(1)

    # Run batch import
    try:
        stats, report = batch_import_images(
            directory=directory,
            progress_interval=args.progress_interval,
            owner_name=args.owner,
            owner_contact=args.contact
        )

        # Save report
        report_path = report.save_to_file(stats)
        print(f"Process report saved to: {report_path}")

        # Exit with appropriate code
        if stats.failed > 0:
            sys.exit(1)  # Non-zero exit code if there were failures
        else:
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Fatal error during batch import: {e}")
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
