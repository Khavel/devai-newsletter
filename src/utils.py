"""Shared utilities: logging, rate limiting, HTTP retry, Markdown conversion."""

import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Path) -> None:
    """Configure root logger to write to stdout and a daily log file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console (INFO+) — force UTF-8 so Windows cp1252 doesn't choke
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    if hasattr(ch.stream, "reconfigure"):
        try:
            ch.stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    root.addHandler(ch)

    # File (DEBUG+)
    date_str = datetime.now().strftime("%Y%m%d")
    fh = logging.FileHandler(
        log_dir / f"pipeline_{date_str}.log", encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple token-bucket rate limiter (blocking)."""

    def __init__(self, calls_per_second: float = 1.0) -> None:
        self._interval = 1.0 / calls_per_second
        self._last: float = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last = time.monotonic()


# ---------------------------------------------------------------------------
# HTTP retry decorator
# ---------------------------------------------------------------------------

def http_retry(func):
    """Decorator: exponential back-off retry for transient HTTP errors."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )(func)


# ---------------------------------------------------------------------------
# Markdown → HTML (email-safe subset)
# ---------------------------------------------------------------------------

def markdown_to_html(text: str) -> str:
    """Convert the simple Markdown Claude produces into email-safe HTML.

    Handles: **bold**, *italic*, [text](url), and paragraph breaks.
    """
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.DOTALL)
    # Italic (avoid matching lone asterisks in URLs)
    text = re.sub(r"\*([^*\n]+?)\*", r"<em>\1</em>", text)
    # Links — inline style for email clients that strip <head> CSS
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\)]+)\)",
        r'<a href="\2" style="color:#2563eb;text-decoration:underline;">\1</a>',
        text,
    )
    # Split into paragraphs and wrap
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    parts = [
        f'<p style="margin:0 0 10px 0;padding:0;line-height:1.85;">{p}</p>'
        for p in paragraphs
    ]
    return "\n".join(parts)


def markdown_to_plain(text: str) -> str:
    """Strip Markdown formatting for plaintext email version."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\*([^*\n]+?)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r"\1 (\2)", text)
    return text.strip()
