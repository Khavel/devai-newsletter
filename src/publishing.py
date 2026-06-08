"""Phase 5 — Publishing: open browser preview, push draft to MailerLite, publish to Ghost."""

import hashlib
import hmac
import json
import logging
import os
import re
import struct
import time
import webbrowser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from .utils import RateLimiter

logger = logging.getLogger(__name__)
_rl = RateLimiter(calls_per_second=1.0)

_MAILERLITE_API = "https://connect.mailerlite.com/api"
_NEWSLETTER_FEATURE_IMAGE = "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80"


def _clamp(text: str, max_len: int) -> str:
    """Trim text at a word boundary for SEO fields."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def _strip_md(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`#>]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _format_human_date(date_str: str) -> str:
    try:
        from datetime import datetime

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{dt.day} {dt.strftime('%b %Y').lower()}"
    except Exception:
        return date_str


def _load_article_data(date_str: str, html_file: Path | None = None) -> dict:
    candidates: list[Path] = []
    if html_file:
        candidates.append(html_file.parent.parent / "data" / f"articles_{date_str}.json")
    candidates.append(Path(__file__).parent.parent / "data" / f"articles_{date_str}.json")

    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _article_heading(item: dict) -> str:
    content = item.get("content", "")
    match = re.search(r"\*\*(.+?)\*\*", content)
    return _strip_md(match.group(1) if match else item.get("original_title", ""))


def _build_newsletter_seo(config: dict, date_str: str, article_data: dict) -> dict[str, str]:
    nl_cfg = config.get("newsletter", {})
    name = nl_cfg.get("name", "DevAI")
    human_date = _format_human_date(date_str)

    items = list(article_data.get("articles", []))
    if article_data.get("repo_of_week"):
        items.append(article_data["repo_of_week"])
    topics = [_article_heading(item) for item in items]
    topics = [topic for topic in topics if topic]

    if topics:
        topic_line = ", ".join(topics[:3])
        title = _clamp(f"{name}: {topic_line} | {human_date}", 65)
        description = _clamp(
            f"Newsletter para desarrolladores: {topic_line}. "
            "Novedades de Claude Code, Cursor, GitHub Copilot y herramientas de IA "
            "que afectan tu workflow de programación.",
            155,
        )
    else:
        title = _clamp(f"{name}: herramientas de IA para desarrolladores | {human_date}", 65)
        description = _clamp(
            "Newsletter semanal en español sobre Claude Code, Cursor, GitHub Copilot, "
            "MCP y herramientas de IA para desarrolladores.",
            155,
        )

    return {
        "title": title,
        "meta_title": title,
        "meta_description": description,
        "custom_excerpt": description,
        "og_title": title,
        "og_description": description,
    }


def _append_utm(url: str, source: str, medium: str, campaign: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("utm_source", source)
    query.setdefault("utm_medium", medium)
    query.setdefault("utm_campaign", campaign)
    return urlunparse(parsed._replace(query=urlencode(query)))


# ---------------------------------------------------------------------------
# MailerLite draft campaign
# ---------------------------------------------------------------------------

def _publish_mailerlite(
    html_content: str, config: dict, date_str: str, seo: dict[str, str] | None = None
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

    # Prefer the AI-generated email subject (top open-rate lever); fall back to SEO title / date.
    gen_subject = (_load_article_data(date_str).get("subject") or "").strip()
    if gen_subject:
        subject = gen_subject
    else:
        subject = seo.get("title") if seo else f"{name} — {human_date}"
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


_AUTO_TAGS: dict[str, str] = {
    "claude code":    "Claude Code",
    "cursor":         "Cursor",
    "copilot":        "GitHub Copilot",
    "github copilot": "GitHub Copilot",
    "mcp":            "MCP",
    "vibe coding":    "Vibe Coding",
    "gemini":         "Gemini",
    "openai":         "OpenAI",
    "devin":          "Devin",
    "bolt.new":       "Bolt",
    "replit":         "Replit",
}


def _build_auto_tags(html_content: str) -> list[dict]:
    """Return Ghost tag objects detected from newsletter content."""
    content_lower = html_content.lower()
    seen: set[str] = set()
    tags = [{"name": "Newsletter", "slug": "newsletter"}]
    for keyword, tag_name in _AUTO_TAGS.items():
        if keyword in content_lower and tag_name not in seen:
            seen.add(tag_name)
            tags.append({"name": tag_name, "slug": tag_name.lower().replace(" ", "-")})
    return tags


def _build_json_ld(title: str, description: str, date_str: str, ghost_base_url: str, slug: str) -> str:
    """Generate NewsArticle JSON-LD for enhanced Google indexing."""
    data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": description,
        "author": {"@type": "Organization", "name": "DevAI", "url": ghost_base_url},
        "publisher": {"@type": "Organization", "name": "DevAI", "url": ghost_base_url},
        "datePublished": date_str,
        "mainEntityOfPage": f"{ghost_base_url}/{slug}/",
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def _publish_ghost(
    html_content: str, config: dict, date_str: str, seo: dict[str, str] | None = None
) -> str | None:
    """Publish newsletter as a Ghost post. Returns the post URL, or None if skipped."""
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    ghost_url     = os.getenv("GHOST_URL", "").strip().rstrip("/")

    if not admin_api_key or not ghost_url:
        logger.warning("GHOST_ADMIN_API_KEY or GHOST_URL not set — skipping Ghost publish.")
        return None

    nl_cfg  = config.get("newsletter", {})
    name    = nl_cfg.get("name", "DevAI Semanal")

    human_date = _format_human_date(date_str)
    title = seo.get("title") if seo else f"{name} — {human_date}"
    slug  = f"newsletter-{date_str}"

    # Extract only <body> content — avoids nested-document width explosion in Ghost
    email_body = _extract_email_body(html_content)

    # Inject internal links to evergreen guides (first mention per keyword)
    from .internal_linking import inject_internal_links
    email_body = inject_internal_links(email_body, ghost_url)

    # Embed in a Ghost HTML card (mobiledoc)
    mobiledoc = json.dumps({
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": email_body}]],
        "markups": [],
        "sections": [[10, 0]],
    })

    # Per-post CSS + NewsArticle JSON-LD for SEO
    description = (seo.get("meta_description") or "") if seo else ""
    json_ld = _build_json_ld(title, description, date_str, ghost_url, slug)
    post_css = (
        "<style>"
        ".gh-article-header{display:none!important}"
        ".gh-article-meta{display:none!important}"
        ".gh-content.gh-canvas{padding-top:0!important}"
        ".gh-article{padding-top:0!important}"
        "</style>"
    )
    codeinjection_head = json_ld + post_css

    # Auto-detect topic tags from newsletter content
    tags = _build_auto_tags(html_content)

    post_payload = {
        "posts": [{
            "title":              title,
            "slug":               slug,
            "status":             "published",
            "mobiledoc":          mobiledoc,
            "codeinjection_head": codeinjection_head,
            "custom_excerpt":      seo.get("custom_excerpt") if seo else None,
            "meta_title":          seo.get("meta_title") if seo else None,
            "meta_description":    seo.get("meta_description") if seo else None,
            "og_title":            seo.get("og_title") if seo else None,
            "og_description":      seo.get("og_description") if seo else None,
            "feature_image":       _NEWSLETTER_FEATURE_IMAGE,
            "tags":                tags,
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
    article_data = _load_article_data(date_str, html_file)
    seo = _build_newsletter_seo(config, date_str, article_data)

    if mode == "draft":
        logger.info("Publishing to Ghost and MailerLite…")
        ghost_post_url    = _publish_ghost(html_content, config, date_str, seo)
        mailerlite_url    = _publish_mailerlite(html_content, config, date_str, seo)
        share_url         = _append_utm(ghost_post_url, "telegram", "social", f"newsletter_{date_str}") if ghost_post_url else None
        _notify_telegram(
            html_file, config, date_str,
            mailerlite_url=mailerlite_url,
            ghost_url=share_url or ghost_post_url,
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
