"""Ghost growth maintenance helpers.

Updates published newsletter posts with search-friendly metadata and writes
evergreen article ideas mined from the same posts.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"


STOP_LINES = {
    "devai",
    "herramientas de ia para devs, en espanol",
    "herramientas de ia para devs, en español",
    "edicion semanal",
    "edición semanal",
    "leer mas",
    "leer más",
    "ver en github",
    "repo de la semana",
    "ediciones anteriores",
    "responder al editor",
    "cancelar suscripcion",
    "cancelar suscripción",
    "escrita por alex cada semana",
    "industria",
    "herramienta",
    "workflow",
    "lanzamiento",
    "actualizacion",
    "actualización",
    "repo",
    "hacker news",
    "github",
    "github trending",
}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def ghost_jwt(admin_api_key: str) -> str:
    key_id, secret = admin_api_key.split(":", 1)
    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    now = int(time.time())
    payload = {"iat": now, "exp": now + 5 * 60, "aud": "/admin/"}
    body = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    sig = hmac.new(bytes.fromhex(secret), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64url(sig)}"


def headers(admin_api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Ghost {ghost_jwt(admin_api_key)}",
        "Content-Type": "application/json",
        "Accept-Version": "v5.0",
    }


def clamp(text: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    line = unicodedata.normalize("NFC", line)
    line = line.replace("ń", "ñ").replace("Ń", "Ñ")
    line = unicodedata.normalize("NFD", line)
    line = line.replace("n\u0301", "ñ").replace("N\u0301", "Ñ")
    line = unicodedata.normalize("NFC", line)
    return line.strip(" -·•")


def normalize(line: str) -> str:
    return clean_line(line).lower()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", clean_line(text))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:70]


def extract_topics(plaintext: str) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()

    for raw in plaintext.splitlines():
        line = clean_line(raw)
        norm = normalize(line)
        if not line or norm in STOP_LINES:
            continue
        if re.match(r"^\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4}$", norm):
            continue
        if len(line) < 18 or len(line) > 82:
            continue
        if line.endswith("."):
            continue
        if re.search(r"\b(de|del|para|con|sin|como|que|ia|ai|code|copilot|cursor|claude|mcp|github|vscode|vs code)\b", norm) is None:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        topics.append(line)
        if len(topics) >= 7:
            break

    return topics


def date_from_slug(slug: str) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", slug)
    if not match:
        return slug
    try:
        dt = datetime.strptime(match.group(1), "%Y-%m-%d")
        return f"{dt.day} {dt.strftime('%b %Y').lower()}"
    except ValueError:
        return match.group(1)


def build_newsletter_seo(post: dict) -> dict[str, str]:
    topics = extract_topics(post.get("plaintext") or "")
    human_date = date_from_slug(post.get("slug", ""))
    if topics:
        topic_line = ", ".join(topics[:3])
        title = clamp(f"DevAI: {topic_line} | {human_date}", 65)
        description = clamp(
            f"Resumen semanal para desarrolladores: {topic_line}. "
            "Novedades de IA, herramientas de coding y cambios que afectan a tu workflow.",
            155,
        )
    else:
        title = clamp(f"DevAI: herramientas de IA para desarrolladores | {human_date}", 65)
        description = (
            "Newsletter semanal en español sobre Claude Code, Cursor, GitHub Copilot, "
            "MCP y herramientas de IA para desarrolladores."
        )
    return {
        "title": title,
        "custom_excerpt": description,
        "meta_title": title,
        "meta_description": description,
    }


def evergreen_ideas(posts: list[dict]) -> list[dict[str, str]]:
    ideas: list[dict[str, str]] = []
    seen: set[str] = set()
    for post in posts:
        for topic in extract_topics(post.get("plaintext") or "")[:4]:
            key = normalize(topic)
            if key in seen:
                continue
            seen.add(key)
            ideas.append(
                {
                    "source": post["slug"],
                    "title": topic,
                    "slug": slugify(topic),
                    "angle": f"Convertir el bloque de newsletter en una guia evergreen sobre {topic}.",
                }
            )
    return ideas


def fetch_newsletter_posts(client: httpx.Client, ghost_url: str, admin_api_key: str) -> list[dict]:
    params = {
        "filter": "tag:newsletter",
        "limit": "all",
        "formats": "plaintext",
        "fields": "id,slug,title,custom_excerpt,updated_at,published_at,plaintext",
        "order": "published_at desc",
    }
    resp = client.get(
        f"{ghost_url}/ghost/api/admin/posts/",
        headers=headers(admin_api_key),
        params=params,
    )
    resp.raise_for_status()
    return resp.json().get("posts", [])


def update_post(client: httpx.Client, ghost_url: str, admin_api_key: str, post: dict, seo: dict[str, str]) -> None:
    payload = {"posts": [{**seo, "updated_at": post["updated_at"]}]}
    resp = client.put(
        f"{ghost_url}/ghost/api/admin/posts/{post['id']}/",
        headers=headers(admin_api_key),
        json=payload,
    )
    resp.raise_for_status()


def write_report(ideas: list[dict[str, str]]) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "evergreen_opportunities.md"
    lines = [
        "# Evergreen opportunities",
        "",
        "Ideas extraidas de newsletters publicadas para convertir en articulos SEO.",
        "",
    ]
    for idea in ideas:
        lines.extend(
            [
                f"## {idea['title']}",
                "",
                f"- Source: `{idea['source']}`",
                f"- Suggested slug: `{idea['slug']}`",
                f"- Angle: {idea['angle']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Update newsletter metadata in Ghost")
    parser.add_argument("--report", action="store_true", help="Write evergreen opportunities report")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    ghost_url = os.getenv("GHOST_URL", "").strip().rstrip("/")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not ghost_url or not admin_api_key:
        raise SystemExit("GHOST_URL and GHOST_ADMIN_API_KEY are required")

    with httpx.Client(timeout=30) as client:
        posts = fetch_newsletter_posts(client, ghost_url, admin_api_key)
        print(f"Found {len(posts)} newsletter posts")
        for post in posts:
            seo = build_newsletter_seo(post)
            print(f"- {post['slug']}: {seo['title']} / {seo['meta_description']}")
            if args.apply:
                update_post(client, ghost_url, admin_api_key, post, seo)

    if args.report:
        path = write_report(evergreen_ideas(posts))
        print(f"Report written: {path}")


if __name__ == "__main__":
    main()
