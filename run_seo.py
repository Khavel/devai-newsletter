#!/usr/bin/env python3
"""DevAI SEO Intelligence — GSC gap analysis pipeline.

Usage:
  python run_seo.py               # run full pipeline
  python run_seo.py --days 90     # custom lookback window
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from src.utils import setup_logging
from src import seo_intelligence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DevAI SEO Intelligence — GSC content gap analysis",
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="Lookback window in days (default: from config or 28)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory (default: output/seo/)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if args.days:
        config.setdefault("seo", {})["lookback_days"] = args.days

    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent / "output" / "seo"
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(output_dir)
    logger = logging.getLogger(__name__)

    date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        report_path = seo_intelligence.run(config, output_dir, date_str)
        logger.info(f"Done! Report at: {report_path}")
        print(f"\n✅ SEO report generated: {report_path}")
        return 0
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
