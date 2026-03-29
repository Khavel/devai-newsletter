"""Phase 5 — Publishing: open browser preview, push draft to MailerLite, publish to Ghost."""

import hashlib
import hmac
import json
import logging
import os
import struct
import time
import webbrowser
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

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
    """Create and auto-send a campaign in MailerLite. Returns the campaign URL, or None if skipped."""
    api_key      = os.getenv("MAILERLITE_API_KEY", "").strip()
    sender_email = os.getenv("MAILERLITE_SENDER_EMAIL", "").strip()
    sender_name  = os.getenv("MAILERLITE_SENDER_NAME", "DevAI").strip()
    group_id     = os.getenv("MAILERLITE_GROUP_ID", "").strip()   # subscriber list ID

    if not api_key:
        logger.warning("MAILERLITE_API_KEY not set — skipping MailerLite.")
        return None
    if not sender_email:
        logger.warning("MAILERLITE_SENDER_EMAIL not set — skipping MailerLite.")
        return None

    nl_cfg  = config.get("newsletter", {})
    name    = nl_cfg.get("name", "DevAI")
    tagline = nl_cfg.get("tagline", "")

    # Human-readable date for the subject line (e.g. "29 mar 2026")
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        try:
            human_date = dt.strftime("%-d %b %Y").lower()   # Linux
        except ValueError:
            human_date = dt.strftime("%#d %b %Y").lower()   # Windows
    except Exception:
        human_date = date_str

    subject = f"{name} — {human_date}"
    if tagline:
        subject += f" · {tagline}"

    ml_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    # --- 1. Create campaign ---
    payload: dict = {
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
    if group_id:
        payload["groups"] = [group_id]

    _rl.wait()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{_MAILERLITE_API}/campaigns",
            headers=ml_headers,
            json=payload,
        )
        if resp.status_code not in (200, 201):
            logger.error(f"MailerLite create error {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
        data = resp.json()

    campaign_id  = data.get("data", {}).get("id", "unknown")
    campaign_url = f"https://dashboard.mailerlite.com/campaigns/{campaign_id}/edit"
    logger.info(f"MailerLite campaign created: {campaign_id}")

    # --- 2. Auto-send (only if group_id is configured) ---
    if group_id and campaign_id != "unknown":
        _rl.wait()
        with httpx.Client(timeout=30) as client:
            send_resp = client.post(
                f"{_MAILERLITE_API}/campaigns/{campaign_id}/schedule",
                headers=ml_headers,
                json={"delivery": "instant"},
            )
        if send_resp.status_code in (200, 201):
            logger.info(f"MailerLite campaign sent instantly: {campaign_id}")
            print(f"\n{'='*60}")
            print(f"[OK] Newsletter enviada en MailerLite!")
            print(f"   Campaign ID : {campaign_id}")
            print(f"   URL         : {campaign_url}")
            print(f"{'='*60}\n")
        else:
            logger.warning(f"MailerLite send failed {send_resp.status_code}: {send_resp.text[:300]}")
            print(f"\n{'='*60}")
            print(f"[OK] Draft creado en MailerLite (envío manual necesario)")
            print(f"   Revisar: {campaign_url}")
            print(f"{'='*60}\n")
    else:
        # No group configured — leave as draft
        print(f"\n{'='*60}")
        print(f"[OK] Draft creado en MailerLite (sin grupo configurado)")
        print(f"   Campaign ID : {campaign_id}")
        print(f"   Revisar     : {campaign_url}")
        print(f"{'='*60}\n")

    return campaign_url


# ---------------------------------------------------------------------------
# Ghost publish
# ---------------------------------------------------------------------------

def _extract_email_body(full_html: str) -> str:
    """Strip <html>/<head>/<body> wrapper from email HTML so it embeds cleanly in Ghost."""
    soup = BeautifulSoup(full_html, "lxml")
    styles = "".join(str(s) for s in soup.find_all("style"))
    body = soup.find("body")
    if not body:
        return full_html
    body_style = body.get("style", "margin:0;padding:0;background-color:#f1f5f9")
    return f'{styles}<div style="{body_style}">{body.decode_contents()}</div>'


def _ghost_jwt(admin_api_key: str) -> str:
    """Generate a short-lived JWT for the Ghost Admin API (no external lib needed)."""
    import base64

    key_id, secret_hex = admin_api_key.split(":")
    secret = bytes.fromhex(secret_hex)

    now = int(time.time())
    header  = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    payload = {"iat": now, "exp": now + 300, "aud": "/admin/"}

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    h = b64url(json.dumps(header,  separators=(",", ":")).encode())
    p = b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64url(sig)}"


def _publish_ghost(
    html_content: str, config: dict, date_str: str
) -> str | None:
    """Publish newsletter as a Ghost post. Returns the post URL, or None if skipped."""
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    ghost_url     = os.getenv("GHOST_URL", "").strip().rstrip("/")

    if not admin_api_key or not ghost_url:
        logger.warning("GHOST_ADMIN_API_KEY or GHOST_URL not set — skipping Ghost publish.")
        return None

    nl_cfg  = config.get("newsletter", {})
    name    = nl_cfg.get("name", "DevAI Semanal")

    # Human-readable date
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day = str(dt.day)
        human_date = f"{day} {dt.strftime('%b %Y').lower()}"
    except Exception:
        human_date = date_str

    title = f"{name} — {human_date}"
    slug  = f"newsletter-{date_str}"

    # Extract only <body> content — avoids nested-document width explosion in Ghost
    email_body = _extract_email_body(html_content)

    # Embed in a Ghost HTML card (mobiledoc)
    mobiledoc = json.dumps({
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": email_body}]],
        "markups": [],
        "sections": [[10, 0]],
    })

    # Per-post CSS: hide Ghost post header/meta, remove top padding
    post_css = (
        "<style>"
        ".gh-article-header{display:none!important}"
        ".gh-article-meta{display:none!important}"
        ".gh-content.gh-canvas{padding-top:0!important}"
        ".gh-article{padding-top:0!important}"
        "</style>"
    )

    post_payload = {
        "posts": [{
            "title":              title,
            "slug":               slug,
            "status":             "published",
            "mobiledoc":          mobiledoc,
            "codeinjection_head": post_css,
            "tags":               [{"name": "Newsletter", "slug": "newsletter"}],
        }]
    }

    token = _ghost_jwt(admin_api_key)
    headers = {
        "Authorization":  f"Ghost {token}",
        "Content-Type":   "application/json",
        "Accept-Version": "v5.0",
    }

    _rl.wait()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{ghost_url}/ghost/api/admin/posts/",
            headers=headers,
            json=post_payload,
        )
        if resp.status_code not in (200, 201):
            logger.error(f"Ghost API error {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
        data = resp.json()

    post_url = data["posts"][0]["url"]
    logger.info(f"Ghost post published: {post_url}")

    print(f"\n{'='*60}")
    print(f"[OK] Newsletter publicada en Ghost!")
    print(f"   URL : {post_url}")
    print(f"{'='*60}\n")
    return post_url


# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------

def _notify_telegram(
    html_file: Path, config: dict, date_str: str,
    mailerlite_url: str | None = None,
    ghost_url: str | None = None,
) -> None:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        logger.debug("Telegram not configured — skipping notification")
        return

    nl_cfg = config.get("newsletter", {})
    name   = nl_cfg.get("name", "DevAI")

    lines = [f"<b>{name} Newsletter — {date_str}</b>\n"]

    if ghost_url:
        lines.append(f"🌐 Web: {ghost_url}")
    if mailerlite_url:
        group_id = os.getenv("MAILERLITE_GROUP_ID", "").strip()
        if group_id:
            lines.append(f"✉️ Email enviado automáticamente")
            lines.append(f"   Ver campaña: {mailerlite_url}")
        else:
            lines.append(f"📋 Draft MailerLite — revisar y enviar: {mailerlite_url}")
    if not ghost_url and not mailerlite_url:
        lines.append(f"Pipeline completado. HTML: <code>{html_file.name}</code>")

    text = "\n".join(lines)

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
        logger.info("Publishing to Ghost and MailerLite…")
        ghost_post_url    = _publish_ghost(html_content, config, date_str)
        mailerlite_url    = _publish_mailerlite(html_content, config, date_str)
        _notify_telegram(
            html_file, config, date_str,
            mailerlite_url=mailerlite_url,
            ghost_url=ghost_post_url,
        )

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
