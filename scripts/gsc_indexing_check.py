"""Submit sitemap and inspect recently published DevAI URLs in Search Console.

Google does not provide an official API equivalent to the URL Inspection
"Request indexing" button for normal blog posts. The supported automation path
is to keep the sitemap fresh, submit it through the Search Console API, and use
URL Inspection API to verify whether Google has indexed each URL.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

from publish_evergreen_articles import GHOST_URL, headers as ghost_headers


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://devaisemanal.com/"
SITEMAP_URL = "https://devaisemanal.com/sitemap.xml"
SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def get_gsc_access_token() -> str:
    """Get a Search Console token with sitemap submit + inspect permissions."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = ROOT / "token-webmasters.json"
    client_path = ROOT / os.getenv("GSC_OAUTH_CLIENT_JSON", "gsc-oauth-client.json")

    if not client_path.exists():
        raise FileNotFoundError(f"OAuth client JSON not found at {client_path}")

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return creds.token


def fetch_recent_published_urls(days: int) -> list[str]:
    """Fetch published Ghost post URLs from the last N days."""
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not admin_api_key:
        raise SystemExit("GHOST_ADMIN_API_KEY is required")

    cutoff = datetime.now(UTC) - timedelta(days=days)
    urls: list[str] = []

    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{GHOST_URL}/ghost/api/admin/posts/",
            headers=ghost_headers(admin_api_key),
            params={
                "filter": "status:published",
                "fields": "slug,url,published_at",
                "limit": "all",
            },
        )
        response.raise_for_status()

    for post in response.json().get("posts", []):
        published_at = post.get("published_at")
        if not published_at:
            continue
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if published >= cutoff and post.get("url"):
            urls.append(post["url"])

    return sorted(set(urls))


def submit_sitemap(client: httpx.Client, access_token: str) -> None:
    """Submit the sitemap to Search Console."""
    site = quote(SITE_URL, safe="")
    feedpath = quote(SITEMAP_URL, safe="")
    response = client.put(
        f"https://www.googleapis.com/webmasters/v3/sites/{site}/sitemaps/{feedpath}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    print(f"submitted sitemap: {SITEMAP_URL}")


def inspect_url(client: httpx.Client, access_token: str, url: str) -> dict:
    response = client.post(
        "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"inspectionUrl": url, "siteUrl": SITE_URL},
    )
    response.raise_for_status()
    result = response.json().get("inspectionResult", {}).get("indexStatusResult", {})
    return {
        "url": url,
        "verdict": result.get("verdict", "?"),
        "coverage": result.get("coverageState", "?"),
        "last_crawl": result.get("lastCrawlTime", "never"),
        "sitemaps": result.get("sitemap", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14, help="Inspect posts published in the last N days")
    parser.add_argument("--url", action="append", default=[], help="Specific URL to inspect; can be repeated")
    parser.add_argument("--no-sitemap-submit", action="store_true")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    access_token = get_gsc_access_token()
    urls = sorted(set(args.url or fetch_recent_published_urls(args.days)))

    with httpx.Client(timeout=30) as client:
        if not args.no_sitemap_submit:
            submit_sitemap(client, access_token)
            time.sleep(1)

        print(f"inspecting urls: {len(urls)}")
        results = [inspect_url(client, access_token, url) for url in urls]

    for row in results:
        status = "OK" if row["verdict"] == "PASS" else "MISS"
        crawl = row["last_crawl"][:10] if row["last_crawl"] != "never" else "never"
        print(f"{status:4s} | {row['url']} | {row['coverage']} | {crawl}")

    out_path = ROOT / "output" / f"gsc_indexing_{datetime.now().strftime('%Y-%m-%d')}.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out_path}")


if __name__ == "__main__":
    main()
