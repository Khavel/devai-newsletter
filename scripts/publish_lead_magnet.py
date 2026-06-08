"""Publish the gated lead-magnet guide (members-only) + CTA it on top-traffic posts.

Lead magnet: "Claude Code vs Cursor" as a members-only Ghost page (subscribe-to-read).
CTA placement chosen from GA4: the two highest-traffic posts are the GitHub Copilot
credits/pricing pages — tool-shoppers comparing on cost, the ideal audience for a
"which tool" comparison. Idempotent (safe to re-run).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_evergreen_articles import GHOST_URL, build_lexical, headers, html_card  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GUIDE_JSON = ROOT / "guides" / "claude-code-vs-cursor.json"
LEAD_SLUG = "guias-claude-code-vs-cursor"
LEAD_PATH = f"/{LEAD_SLUG}/"
CTA_MARKER = "lead-magnet-cc-vs-cursor"
CTA_TARGETS = [
    "github-copilot-ai-credits-tokens-junio-2026",
    "github-copilot-ai-credits-pago-por-uso",
]


def _strip_leading_h1(s: str) -> str:
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", s, count=1, flags=re.I | re.S)


def _get(client: httpx.Client, key: str, kind: str, slug: str) -> dict | None:
    r = client.get(
        f"{GHOST_URL}/ghost/api/admin/{kind}/",
        headers=headers(key),
        params={"filter": f"slug:{slug}", "formats": "lexical", "limit": "1"},
    )
    r.raise_for_status()
    items = r.json().get(kind, [])
    return items[0] if items else None


def publish_lead_magnet(client: httpx.Client, key: str) -> str:
    d = json.loads(GUIDE_JSON.read_text(encoding="utf-8"))
    payload = {
        "title": d["title"],
        "slug": LEAD_SLUG,
        "status": "published",
        "visibility": "members",  # the gate: subscribe (free) to read the full guide
        "custom_excerpt": (d.get("meta_description") or "")[:290],
        "meta_title": d.get("meta_title"),
        "meta_description": d.get("meta_description"),
        "og_title": d.get("og_title"),
        "og_description": d.get("og_description"),
        "feature_image": d.get("feature_image"),
        "tags": [{"name": "Guías", "slug": "guias"}, {"name": "comparativas", "slug": "comparativas"}],
        "lexical": build_lexical([html_card(_strip_leading_h1(d["html"]))]),
    }
    existing = _get(client, key, "pages", LEAD_SLUG)
    if existing:
        payload["updated_at"] = existing["updated_at"]
        r = client.put(f"{GHOST_URL}/ghost/api/admin/pages/{existing['id']}/", headers=headers(key), json={"pages": [payload]})
        action = "updated"
    else:
        r = client.post(f"{GHOST_URL}/ghost/api/admin/pages/", headers=headers(key), json={"pages": [payload]})
        action = "created"
    r.raise_for_status()
    return f"{action}: {r.json()['pages'][0]['url']}  (visibility=members)"


def _cta_html() -> str:
    return (
        f'<div data-cta="{CTA_MARKER}" style="background:#0f172a;border-radius:12px;padding:24px 26px;margin:30px 0;">'
        f'<p style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#38bdf8;margin:0 0 8px;">¿Claude Code o Cursor?</p>'
        f'<p style="color:#e2e8f0;font-size:17px;line-height:1.5;margin:0 0 16px;">Antes de pagar por créditos, mira la comparativa completa: precio, autonomía, interfaz y casos de uso reales.</p>'
        f'<a href="{LEAD_PATH}?utm_source=evergreen&amp;utm_medium=cta&amp;utm_campaign=lead-magnet" '
        f'style="display:inline-block;background:#38bdf8;color:#0f172a;font-weight:750;text-decoration:none;padding:12px 22px;border-radius:8px;">'
        f'Leer la comparativa gratis →</a>'
        f'<p style="color:#94a3b8;font-size:13px;margin:12px 0 0;">Gratis al suscribirte al newsletter.</p></div>'
    )


def add_cta(client: httpx.Client, key: str, slug: str) -> str:
    post = _get(client, key, "posts", slug)
    if not post:
        return f"  MISSING post: {slug}"
    lex = json.loads(post["lexical"])
    children = lex["root"]["children"]
    if any(c.get("type") == "html" and CTA_MARKER in c.get("html", "") for c in children):
        return f"  already has CTA: {slug}"
    insert_at = min(3, len(children))  # mid-upper, after the reader gets some value
    children[insert_at:insert_at] = [html_card(_cta_html())]
    lex["root"]["children"] = children
    r = client.put(
        f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
        headers=headers(key),
        json={"posts": [{"lexical": json.dumps(lex, ensure_ascii=False), "updated_at": post["updated_at"]}]},
    )
    r.raise_for_status()
    return f"  CTA added: {slug}"


def main() -> None:
    load_dotenv(ROOT / ".env")
    key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not key:
        raise SystemExit("GHOST_ADMIN_API_KEY required")
    with httpx.Client(timeout=30) as client:
        print("lead magnet " + publish_lead_magnet(client, key))
        print("CTAs:")
        for slug in CTA_TARGETS:
            print(add_cta(client, key, slug))


if __name__ == "__main__":
    main()
