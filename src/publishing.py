"""Phase 5 — Publishing: open browser preview or push draft to Beehiiv."""

import logging
import os
import webbrowser
from pathlib import Path

import httpx

from .utils import RateLimiter

logger = logging.getLogger(__name__)
_rl = RateLimiter(calls_per_second=1.0)


# ---------------------------------------------------------------------------
# Beehiiv draft
# ---------------------------------------------------------------------------

def _publish_beehiiv(
    html_content: str, txt_content: str, config: dict, date_str: str
) -> None:
    api_key = os.getenv("BEEHIIV_API_KEY", "").strip()
    pub_id = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()

    if not api_key or not pub_id:
        raise EnvironmentError(
            "BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID must be set in .env "
            "to use --draft mode."
        )

    nl_cfg = config.get("newsletter", {})
    title = f"{nl_cfg.get('name', 'DevAI')} — {date_str}"
    subtitle = nl_cfg.get("tagline", "")

    payload = {
        "title": title,
        "subtitle": subtitle,
        "content_html": html_content,
        "content_plaintext": txt_content,
        "status": "draft",
        "displayed_date": f"{date_str}T09:00:00.000Z",
    }

    _rl.wait()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"https://api.beehiiv.com/v2/publications/{pub_id}/posts",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if resp.status_code not in (200, 201):
            logger.error(f"Beehiiv API error {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
        data = resp.json()

    post_id = data.get("data", {}).get("id", "unknown")
    post_url = f"https://app.beehiiv.com/posts/{post_id}"
    logger.info(f"Beehiiv draft created: {post_url}")

    print(f"\n{'='*60}")
    print(f"[OK] Draft publicado en Beehiiv!")
    print(f"   Post ID : {post_id}")
    print(f"   Revisar : {post_url}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------

def _notify_telegram(html_file: Path, config: dict, date_str: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        logger.debug("Telegram not configured — skipping notification")
        return

    nl_cfg = config.get("newsletter", {})
    name = nl_cfg.get("name", "DevAI")

    text = (
        f"<b>{name} Newsletter — {date_str}</b>\n\n"
        f"Pipeline completado.\n"
        f"Revisa el preview en tu navegador y ejecuta:\n"
        f"<code>python run.py --draft</code>\n\n"
        f"HTML: <code>{html_file.name}</code>"
    )

    _rl.wait()
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
        if resp.status_code == 200:
            logger.info("Telegram notification sent")
        else:
            logger.warning(f"Telegram notification failed: {resp.status_code}")
    except Exception as exc:
        logger.warning(f"Telegram notification error: {exc}")


# ---------------------------------------------------------------------------
# Phase entry point
# ---------------------------------------------------------------------------

def run(config: dict, html_file: Path, txt_file: Path, mode: str) -> None:
    html_content = html_file.read_text(encoding="utf-8")
    txt_content = txt_file.read_text(encoding="utf-8")
    date_str = html_file.stem.replace("newsletter_", "")

    if mode == "draft":
        logger.info("Publishing to Beehiiv as draft…")
        _publish_beehiiv(html_content, txt_content, config, date_str)

    else:  # preview (default)
        file_uri = html_file.resolve().as_uri()
        logger.info(f"Opening preview: {file_uri}")
        webbrowser.open(file_uri)

        print(f"\n{'='*60}")
        print(f"[OK] Newsletter lista!")
        print(f"   HTML : {html_file}")
        print(f"   TXT  : {txt_file}")
        print(f"\n   Para publicar: python run.py --draft")
        print(f"{'='*60}\n")

        _notify_telegram(html_file, config, date_str)
