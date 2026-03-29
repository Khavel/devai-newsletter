#!/usr/bin/env python3
"""DevAI Newsletter — automated pipeline entry point.

Usage:
  python run.py             # preview mode (default): open in browser
  python run.py --preview   # same as above
  python run.py --draft     # publish as draft to Beehiiv
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env with explicit path so it works regardless of CWD
load_dotenv(Path(__file__).parent / ".env", override=True)

from src.utils import setup_logging
from src import sourcing, curation, rewriting, assembly, publishing


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DevAI Newsletter — automated pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  --preview  Generate newsletter and open in browser (default)\n"
            "  --draft    Generate and publish as draft to Beehiiv\n"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--draft", action="store_true", help="Publish draft to Beehiiv")
    mode.add_argument("--preview", action="store_true", help="Preview in browser (default)")
    return parser.parse_args()


def _check_env(mode: str) -> list[str]:  # noqa: ARG001
    """Return list of missing required env vars.

    ANTHROPIC_API_KEY is always required.
    BEEHIIV_* are optional — publishing.py warns and skips if absent.
    """
    return [k for k in ["ANTHROPIC_API_KEY"] if not os.getenv(k)]


def main() -> int:
    args = _parse_args()
    mode = "draft" if args.draft else "preview"

    # Setup project directories
    root = Path(__file__).parent
    data_dir = root / "data"
    output_dir = root / "output"
    log_dir = root / "logs"
    for d in (data_dir, output_dir, log_dir):
        d.mkdir(exist_ok=True)

    setup_logging(log_dir)
    logger = logging.getLogger("run")

    # Load config
    config_path = root / "config.yaml"
    if not config_path.exists():
        print(f"ERROR: config.yaml not found at {config_path}", file=sys.stderr)
        return 1
    config: dict = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # Validate environment
    missing = _check_env(mode)
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        logger.error("Copy .env.example to .env and fill in the required values.")
        return 1

    date_str = datetime.now().strftime("%Y-%m-%d")
    nl_name = config.get("newsletter", {}).get("name", "DevAI")

    logger.info("=" * 60)
    logger.info(f"{nl_name} Newsletter Pipeline | {date_str} | mode={mode}")
    logger.info("=" * 60)

    try:
        # ── Phase 1: Sourcing ────────────────────────────────────────────
        logger.info("[1/5] Sourcing — collecting news from RSS, HN, Reddit, GitHub…")
        raw_file = sourcing.run(config, data_dir, date_str)

        # ── Phase 2: Curation ────────────────────────────────────────────
        logger.info("[2/5] Curation — asking Claude to select the best items…")
        curated_file = curation.run(config, raw_file, data_dir, date_str)

        # ── Phase 3: Rewriting ───────────────────────────────────────────
        logger.info("[3/5] Rewriting — generating article paragraphs with Claude…")
        articles_file = rewriting.run(config, curated_file, data_dir, date_str)

        # ── Phase 4: Assembly ────────────────────────────────────────────
        logger.info("[4/5] Assembly — rendering HTML and plaintext newsletter…")
        html_file, txt_file = assembly.run(config, articles_file, output_dir, date_str)

        # ── Phase 5: Publishing ──────────────────────────────────────────
        logger.info(f"[5/5] Publishing ({mode})…")
        publishing.run(config, html_file, txt_file, mode)

        logger.info("=" * 60)
        logger.info("Pipeline complete!")
        logger.info("=" * 60)
        return 0

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        return 130
    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
