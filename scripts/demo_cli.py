#!/usr/bin/env python3
"""
Demo CLI script for pandoc-ui Phase 1.

Usage:
    python scripts/demo_cli.py examples/article.md -o output.html
    uv run python scripts/demo_cli.py examples/article.md -o output.html
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandoc_ui.app.conversion_service import ConversionService
from pandoc_ui.models import ConversionProfile, OutputFormat


def setup_logging():
    """Configure logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demo CLI for pandoc-ui conversion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_cli.py examples/article.md
  python scripts/demo_cli.py examples/article.md -o output.html
  python scripts/demo_cli.py examples/article.md -f pdf -o article.pdf
        """,
    )

    parser.add_argument("input_file", type=Path, nargs="?", help="Input file to convert")

    parser.add_argument(
        "-o", "--output", type=Path, help="Output file path (auto-generated if not specified)"
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["html", "pdf", "docx", "odt", "epub", "latex", "rtf"],
        default="html",
        help="Output format (default: html)",
    )

    parser.add_argument(
        "--check-pandoc", action="store_true", help="Only check pandoc availability and exit"
    )

    return parser.parse_args()


def main():
    """Main demo function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_arguments()

    # Initialize conversion service
    logger.info("Initializing pandoc-ui conversion service...")
    service = ConversionService()

    # Check pandoc availability
    if not service.is_pandoc_available():
        logger.error("❌ Pandoc is not available on this system")
        logger.error("Please install pandoc from https://pandoc.org/installing.html")
        return 1

    pandoc_info = service.get_pandoc_info()
    logger.info(f"✅ Pandoc detected: {pandoc_info.path} (version {pandoc_info.version})")

    # If only checking pandoc, exit here
    if args.check_pandoc:
        logger.info("Pandoc check completed successfully")
        return 0

    # Validate input file is provided
    if not args.input_file:
        logger.error("❌ Input file is required when not using --check-pandoc")
        return 1

    # Validate input file
    if not service.validate_input_file(args.input_file):
        logger.error(f"❌ Invalid input file: {args.input_file}")
        return 1

    # Create conversion profile
    try:
        output_format = OutputFormat(args.format)
        profile = ConversionProfile(
            input_path=args.input_file, output_path=args.output, output_format=output_format
        )

        # Auto-generate output path if not provided
        if args.output is None:
            profile.output_path = args.input_file.with_suffix(f".{args.format}")

        logger.info(f"📄 Converting: {profile.input_path} -> {profile.output_path}")
        logger.info(f"📋 Format: {profile.output_format.value}")

    except ValueError:
        logger.error(f"❌ Invalid output format: {args.format}")
        return 1

    # Perform conversion
    result = service.convert(profile)

    if result.success:
        logger.info("✅ Conversion completed successfully!")
        logger.info(f"📁 Output saved to: {result.output_path}")
        logger.info(f"⏱️  Duration: {result.duration_seconds:.2f} seconds")

        # Verify output file exists
        if result.output_path and result.output_path.exists():
            file_size = result.output_path.stat().st_size
            logger.info(f"📊 Output file size: {file_size:,} bytes")
        else:
            logger.warning("⚠️  Output file not found after conversion")

        return 0
    else:
        logger.error(f"❌ Conversion failed: {result.error_message}")
        if result.command:
            logger.error(f"🔧 Command: {result.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
