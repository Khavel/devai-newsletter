"""Phase 5 — Publishing: open browser preview or push draft to MailerLite."""

import logging
import os
import webbrowser
from pathlib import Path

import httpx

from .utils import RateLimiter

logger = logging.getLogger(__name__)
_rl = RateLimiter(calls_per_second=1.0)

_MAILERLITE_API = "https://connect.mailerlite.com/api"


# ---------------------------------------------------------------------------
# MailerLite draft campaign
# ---------------------------------------------------------------------------

def _publish_mailerlite(
    html_content: str, config: dict, date_str: str
) -> str | None:
    """Create a draft campaign in MailerLite. Returns the campaign URL, or None if skipped."""
    api_key      = os.getenv("MAILERLITE_API_KEY", "").strip()
    sender_email = os.getenv("MAILERLITE_SENDER_EMAIL", "").strip()
    sender_name  = os.getenv("MAILERLITE_SENDER_NAME", "DevAI").strip()

    if not api_key:
        logger.warning("MAILERLITE_API_KEY not set — skipping MailerLite draft.")
        return None
    if not sender_email:
        logger.warning("MAILERLITE_SENDER_EMAIL not set — skipping MailerLite draft.")
        return None

    nl_cfg  = config.get("newsletter", {})
    name    = nl_cfg.get("name", "DevAI")
    tagline = nl_cfg.get("tagline", "")

    # Human-readable date for the subject line (e.g. "29 mar 2026")
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        human_date = dt.strftime("%-d %b %Y").lower()   # Linux
    except ValueError:
        try:
            human_date = dt.strftime("%#d %b %Y").lower()  # Windows
        except Exception:
            human_date = date_str

    subject = f"{name} — {human_date}"
    if tagline:
        subject += f" · {tagline}"

    payload = {
        "name": f"{name} — {date_str}",
        "type": "regular",
        "emails": [
            {
                "subject":   subject,
                "from_name": sender_name,
                "from":      sender_email,
                "content":   html_content,
            }
        ],
    }

    _rl.wait()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{_MAILERLITE_API}/campaigns",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            json=payload,
        )
        if resp.status_code not in (200, 201):
            logger.error(f"MailerLite API error {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
        data = resp.json()

    campaign_id  = data.get("data", {}).get("id", "unknown")
    campaign_url = f"https://dashboard.mailerlite.com/campaigns/{campaign_id}/edit"
    logger.info(f"MailerLite draft created: {campaign_url}")

    print(f"\n{'='*60}")
    print(f"[OK] Draft creado en MailerLite!")
    print(f"   Campaign ID : {campaign_id}")
    print(f"   Revisar     : {campaign_url}")
    print(f"{'='*60}\n")
    return campaign_url


# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------

def _notify_telegram(
    html_file: Path, config: dict, date_str: str, publish_url: str | None = None
) -> None:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        logger.debug("Telegram not configured — skipping notification")
        return

    nl_cfg = config.get("newsletter", {})
    name   = nl_cfg.get("name", "DevAI")

    if publish_url:
        text = (
            f"<b>{name} Newsletter — {date_str}</b>\n\n"
            f"Draft listo en MailerLite.\n"
            f"Revisar y programar: {publish_url}"
        )
    else:
        text = (
            f"<b>{name} Newsletter — {date_str}</b>\n\n"
            f"Pipeline completado (MailerLite no configurado).\n"
            f"HTML generado: <code>{html_file.name}</code>\n\n"
            f"Configura MAILERLITE_API_KEY y MAILERLITE_SENDER_EMAIL para publicar automaticamente."
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
    date_str     = html_file.stem.replace("newsletter_", "")

    if mode == "draft":
        logger.info("Publishing to MailerLite as draft campaign…")
        publish_url = _publish_mailerlite(html_content, config, date_str)
        _notify_telegram(html_file, config, date_str, publish_url=publish_url)

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
