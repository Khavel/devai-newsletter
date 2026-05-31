"""Publish pre-written evergreen guides to Ghost CMS as Pages or Posts.

Usage:
    python publish_guides.py                      # publish all guides/
    python publish_guides.py guides/claude-code.json  # publish one guide
    python publish_guides.py --list               # list published guides

Guide JSON format:
    {
        "title":            "Claude Code: Guía Definitiva para Desarrolladores (2026)",
        "slug":             "guias/claude-code",
        "type":             "page" | "post",
        "status":           "published" | "draft",
        "tags":             ["guias", "claude-code"],
        "meta_title":       "...",
        "meta_description": "...",
        "og_title":         "...",
        "og_description":   "...",
        "feature_image":    "https://...",
        "html":             "<h2>...</h2><p>...</p>"
    }
"""

import hashlib
import hmac
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

GUIDES_DIR = Path(__file__).parent / "guides"


def _ghost_jwt(admin_api_key: str) -> str:
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


def _html_to_mobiledoc(html: str) -> str:
    return json.dumps({
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": html}]],
        "markups": [],
        "sections": [[10, 0]],
    })


def publish_guide(guide: dict) -> str | None:
    """Publish a single guide to Ghost. Returns the published URL."""
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    ghost_url     = os.getenv("GHOST_URL", "").strip().rstrip("/")

    if not admin_api_key or not ghost_url:
        logger.error("GHOST_ADMIN_API_KEY and GHOST_URL must be set.")
        return None

    guide_type = guide.get("type", "post")
    endpoint   = "pages" if guide_type == "page" else "posts"
    payload_key = endpoint  # "pages" or "posts"

    tags = [{"name": t, "slug": t.lower().replace(" ", "-")} for t in guide.get("tags", [])]

    item = {
        "title":              guide["title"],
        "slug":               guide["slug"],
        "status":             guide.get("status", "published"),
        "mobiledoc":          _html_to_mobiledoc(guide["html"]),
        "meta_title":         guide.get("meta_title"),
        "meta_description":   guide.get("meta_description"),
        "og_title":           guide.get("og_title"),
        "og_description":     guide.get("og_description"),
        "custom_excerpt":     guide.get("meta_description"),
        "feature_image":      guide.get("feature_image"),
        "tags":               tags,
    }

    token = _ghost_jwt(admin_api_key)
    headers = {
        "Authorization":  f"Ghost {token}",
        "Content-Type":   "application/json",
        "Accept-Version": "v5.0",
    }

    time.sleep(1)  # Rate limit
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{ghost_url}/ghost/api/admin/{endpoint}/",
            headers=headers,
            json={payload_key: [item]},
        )

    if resp.status_code not in (200, 201):
        logger.error(f"Ghost API error {resp.status_code} for '{guide['slug']}': {resp.text[:500]}")
        resp.raise_for_status()

    data    = resp.json()
    post_url = data[payload_key][0]["url"]
    logger.info(f"Published [{guide_type}]: {post_url}")
    return post_url


def list_guides() -> None:
    """List all guide JSON files in the guides/ directory."""
    if not GUIDES_DIR.exists():
        print("No guides/ directory found.")
        return
    files = sorted(GUIDES_DIR.glob("*.json"))
    if not files:
        print("No guide files found in guides/")
        return
    for f in files:
        try:
            g = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {f.name:45s}  [{g.get('type','post'):4s}]  {g.get('status','?'):10s}  {g.get('slug','')}")
        except Exception as exc:
            print(f"  {f.name}  (error: {exc})")


def main() -> None:
    args = sys.argv[1:]

    if "--list" in args:
        list_guides()
        return

    if args:
        targets = [Path(a) for a in args]
    else:
        if not GUIDES_DIR.exists():
            logger.error(f"guides/ directory not found at {GUIDES_DIR}")
            sys.exit(1)
        targets = sorted(GUIDES_DIR.glob("*.json"))

    if not targets:
        logger.error("No guide files to publish.")
        sys.exit(1)

    results: list[tuple[str, str | None]] = []
    for path in targets:
        if not path.exists():
            logger.warning(f"File not found: {path}")
            continue
        guide = json.loads(path.read_text(encoding="utf-8"))
        url = publish_guide(guide)
        results.append((guide.get("slug", path.name), url))

    print("\n" + "=" * 60)
    print("PUBLICATION RESULTS")
    print("=" * 60)
    for slug, url in results:
        status = url or "FAILED"
        print(f"  {slug:50s}  {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
