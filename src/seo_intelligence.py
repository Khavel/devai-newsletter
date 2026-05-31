"""SEO Intelligence — GSC queries → Ghost content gap analysis → article suggestions.

Pulls Search Console query data, compares against existing Ghost posts,
and uses Claude to identify high-opportunity content gaps.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx
import jwt
import time

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Google Search Console API
# ---------------------------------------------------------------------------

def _gsc_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_gsc_access_token() -> str:
    """Get access token via OAuth2 desktop flow (caches to token.json)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    project_root = Path(__file__).resolve().parent.parent
    token_path = project_root / "token.json"
    client_path = project_root / os.getenv("GSC_OAUTH_CLIENT_JSON", "gsc-oauth-client.json")

    if not client_path.exists():
        raise FileNotFoundError(
            f"OAuth client JSON not found at {client_path}. "
            "Download it from GCP Console → APIs & Services → Credentials."
        )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), _SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return creds.token


def fetch_gsc_queries(
    site_url: str,
    days: int = 28,
    row_limit: int = 200,
) -> list[dict]:
    """Fetch top queries from Google Search Console API.

    Returns list of {query, clicks, impressions, ctr, position}.
    """
    access_token = get_gsc_access_token()

    end_date = datetime.now() - timedelta(days=3)  # GSC data has ~3 day lag
    start_date = end_date - timedelta(days=days)

    payload = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "dimensions": ["query"],
        "rowLimit": row_limit,
        "dataState": "final",
    }

    encoded_site = quote(site_url, safe="")
    api_url = (
        f"https://www.googleapis.com/webmasters/v3"
        f"/sites/{encoded_site}/searchAnalytics/query"
    )

    with httpx.Client(timeout=30) as client:
        resp = client.post(api_url, json=payload, headers=_gsc_headers(access_token))
        resp.raise_for_status()
        data = resp.json()

    queries = []
    for row in data.get("rows", []):
        queries.append({
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1),
        })

    logger.info(f"GSC: fetched {len(queries)} queries for {site_url} (last {days}d)")
    return queries


def fetch_gsc_pages(
    site_url: str,
    days: int = 28,
    row_limit: int = 100,
) -> list[dict]:
    """Fetch top pages from Google Search Console."""
    access_token = get_gsc_access_token()

    end_date = datetime.now() - timedelta(days=3)
    start_date = end_date - timedelta(days=days)

    payload = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "dimensions": ["page"],
        "rowLimit": row_limit,
        "dataState": "final",
    }

    encoded_site = quote(site_url, safe="")
    api_url = (
        f"https://www.googleapis.com/webmasters/v3"
        f"/sites/{encoded_site}/searchAnalytics/query"
    )

    with httpx.Client(timeout=30) as client:
        resp = client.post(api_url, json=payload, headers=_gsc_headers(access_token))
        resp.raise_for_status()
        data = resp.json()

    pages = []
    for row in data.get("rows", []):
        pages.append({
            "page": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1),
        })

    logger.info(f"GSC: fetched {len(pages)} pages for {site_url}")
    return pages


# ---------------------------------------------------------------------------
# Ghost Content API
# ---------------------------------------------------------------------------

def _ghost_admin_token() -> str:
    """Generate Ghost Admin API JWT token."""
    key = os.getenv("GHOST_ADMIN_API_KEY", "")
    if not key or ":" not in key:
        raise ValueError("GHOST_ADMIN_API_KEY not configured (format: id:secret)")

    kid, secret = key.split(":", 1)
    iat = int(time.time())

    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    payload = {
        "iat": iat,
        "exp": iat + 300,  # 5 min
        "aud": "/admin/",
    }

    return jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers=header)


def fetch_ghost_posts() -> list[dict]:
    """Fetch all published posts from Ghost, including tags.

    Returns list of {title, slug, url, published_at, tags, excerpt}.
    """
    ghost_url = os.getenv("GHOST_URL", "").rstrip("/")
    if not ghost_url:
        raise ValueError("GHOST_URL not configured")

    token = _ghost_admin_token()
    posts = []
    page = 1

    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(
                f"{ghost_url}/ghost/api/admin/posts/",
                params={
                    "limit": 100,
                    "page": page,
                    "fields": "title,slug,url,published_at,custom_excerpt",
                    "include": "tags",
                    "filter": "status:published",
                },
                headers={"Authorization": f"Ghost {token}"},
            )
            resp.raise_for_status()
            data = resp.json()

            for p in data.get("posts", []):
                tags = [t["name"] for t in p.get("tags", [])]
                posts.append({
                    "title": p.get("title", ""),
                    "slug": p.get("slug", ""),
                    "url": p.get("url", ""),
                    "published_at": p.get("published_at", ""),
                    "tags": tags,
                    "excerpt": p.get("custom_excerpt", ""),
                })

            meta = data.get("meta", {}).get("pagination", {})
            if page >= meta.get("pages", 1):
                break
            page += 1

    logger.info(f"Ghost: fetched {len(posts)} published posts")
    return posts


# ---------------------------------------------------------------------------
# Gap Analysis with Claude
# ---------------------------------------------------------------------------

def analyze_gaps(
    queries: list[dict],
    posts: list[dict],
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Use Claude to analyze GSC queries vs existing content and find gaps.

    Returns structured analysis with:
    - content_gaps: queries with no matching content
    - optimization_opportunities: existing content that could rank better
    - suggested_articles: concrete article proposals
    """
    import anthropic

    # Build context strings
    queries_summary = "\n".join(
        f"- \"{q['query']}\" → {q['impressions']} imp, {q['clicks']} clicks, "
        f"CTR {q['ctr']}%, pos {q['position']}"
        for q in sorted(queries, key=lambda x: x["impressions"], reverse=True)[:80]
    )

    posts_summary = "\n".join(
        f"- [{p['published_at'][:10] if p['published_at'] else '?'}] "
        f"\"{p['title']}\" (tags: {', '.join(p['tags']) or 'none'})"
        for p in posts
    )

    prompt = f"""Analyze these Google Search Console queries against our existing blog posts on devaisemanal.com (a Spanish-language site about AI dev tools).

## GSC Queries (last 28 days, sorted by impressions)
{queries_summary}

## Existing Published Posts
{posts_summary}

## Your Task

1. **Content Gaps**: Identify queries where we're getting impressions but have NO dedicated article. Group related queries into topic clusters. Exclude brand-confusion queries (people searching for "devai" as a product unrelated to us, or queries for competitor domains like "devai.dev", "devai.net").

2. **Optimization Opportunities**: Identify queries where we HAVE matching content but position is >10 (page 2+). Suggest specific improvements (title changes, content expansion, etc).

3. **Suggested Articles**: For each content gap, propose a concrete article with:
   - Title (SEO-optimized, in Spanish)
   - Target query cluster
   - Estimated search intent (informational/commercial/navigational)
   - Priority score (1-10, based on impressions × opportunity)
   - Brief outline (3-5 bullet points)

Respond in JSON format:
{{
  "content_gaps": [
    {{
      "topic_cluster": "string",
      "queries": ["query1", "query2"],
      "total_impressions": number,
      "avg_position": number
    }}
  ],
  "optimization_opportunities": [
    {{
      "existing_post": "title",
      "matching_queries": ["query1"],
      "current_position": number,
      "suggestion": "string"
    }}
  ],
  "suggested_articles": [
    {{
      "title": "string (Spanish)",
      "target_queries": ["query1", "query2"],
      "intent": "informational|commercial|navigational",
      "priority": number,
      "outline": ["point1", "point2", "point3"],
      "estimated_impressions": number
    }}
  ],
  "summary": "2-3 sentence executive summary in Spanish"
}}"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    # Extract JSON from response (Claude might wrap it in markdown)
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    try:
        analysis = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("Claude returned non-JSON response, returning raw text")
        analysis = {"raw_response": raw, "parse_error": True}

    logger.info("Gap analysis complete")
    return analysis


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(
    queries: list[dict],
    pages: list[dict],
    posts: list[dict],
    analysis: dict,
    output_path: Path,
) -> Path:
    """Generate a markdown report combining all data."""

    lines = [
        f"# DevAI SEO Intelligence Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    # Summary
    if "summary" in analysis:
        lines.extend([
            "## Resumen",
            "",
            analysis["summary"],
            "",
            "---",
            "",
        ])

    # GSC Overview
    total_clicks = sum(q["clicks"] for q in queries)
    total_impressions = sum(q["impressions"] for q in queries)
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0

    lines.extend([
        "## GSC Overview (últimos 28 días)",
        "",
        f"- **Queries totales:** {len(queries)}",
        f"- **Clics totales:** {total_clicks}",
        f"- **Impresiones totales:** {total_impressions}",
        f"- **CTR medio:** {avg_ctr:.1f}%",
        f"- **Posts publicados en Ghost:** {len(posts)}",
        "",
    ])

    # Top queries table
    lines.extend([
        "### Top Queries por Impresiones",
        "",
        "| Query | Impresiones | Clics | CTR | Posición |",
        "|-------|-------------|-------|-----|----------|",
    ])
    for q in sorted(queries, key=lambda x: x["impressions"], reverse=True)[:20]:
        lines.append(
            f"| {q['query']} | {q['impressions']} | {q['clicks']} | "
            f"{q['ctr']}% | {q['position']} |"
        )
    lines.append("")

    # Content gaps
    gaps = analysis.get("content_gaps", [])
    if gaps:
        lines.extend([
            "---",
            "",
            "## Content Gaps (queries sin artículo dedicado)",
            "",
        ])
        for gap in gaps:
            queries_str = ", ".join(f'"{q}"' for q in gap.get("queries", []))
            lines.extend([
                f"### {gap.get('topic_cluster', 'Unknown')}",
                f"- **Queries:** {queries_str}",
                f"- **Impresiones totales:** {gap.get('total_impressions', '?')}",
                f"- **Posición media:** {gap.get('avg_position', '?')}",
                "",
            ])

    # Optimization opportunities
    opts = analysis.get("optimization_opportunities", [])
    if opts:
        lines.extend([
            "---",
            "",
            "## Oportunidades de Optimización",
            "",
        ])
        for opt in opts:
            lines.extend([
                f"### \"{opt.get('existing_post', '')}\"",
                f"- **Queries:** {', '.join(opt.get('matching_queries', []))}",
                f"- **Posición actual:** {opt.get('current_position', '?')}",
                f"- **Sugerencia:** {opt.get('suggestion', '')}",
                "",
            ])

    # Suggested articles
    articles = analysis.get("suggested_articles", [])
    if articles:
        lines.extend([
            "---",
            "",
            "## Artículos Sugeridos (ordenados por prioridad)",
            "",
        ])
        for i, art in enumerate(
            sorted(articles, key=lambda x: x.get("priority", 0), reverse=True), 1
        ):
            outline = "\n".join(f"  - {p}" for p in art.get("outline", []))
            lines.extend([
                f"### {i}. {art.get('title', 'Sin título')}",
                f"- **Prioridad:** {art.get('priority', '?')}/10",
                f"- **Intent:** {art.get('intent', '?')}",
                f"- **Target queries:** {', '.join(art.get('target_queries', []))}",
                f"- **Impresiones estimadas:** {art.get('estimated_impressions', '?')}",
                f"- **Outline:**",
                outline,
                "",
            ])

    report = "\n".join(lines)
    output_path.write_text(report, encoding="utf-8")
    logger.info(f"Report saved → {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(config: dict, output_dir: Path, date_str: str) -> Path:
    """Run the full SEO intelligence pipeline."""

    seo_config = config.get("seo", {})
    site_url = seo_config.get("gsc_site_url", "https://devaisemanal.com/")
    model = config.get("claude", {}).get("model", "claude-sonnet-4-20250514")
    days = seo_config.get("lookback_days", 28)

    logger.info("=" * 60)
    logger.info(f"SEO Intelligence Pipeline | {date_str}")
    logger.info("=" * 60)

    # Phase 1: Fetch GSC data
    logger.info("[1/4] Fetching GSC queries...")
    queries = fetch_gsc_queries(site_url, days=days)

    logger.info("[1b/4] Fetching GSC pages...")
    pages = fetch_gsc_pages(site_url, days=days)

    # Phase 2: Fetch Ghost posts
    logger.info("[2/4] Fetching Ghost posts...")
    posts = fetch_ghost_posts()

    # Phase 3: Claude gap analysis
    logger.info("[3/4] Running Claude gap analysis...")
    analysis = analyze_gaps(queries, posts, model=model)

    # Phase 4: Generate report
    logger.info("[4/4] Generating report...")
    report_path = output_dir / f"seo_report_{date_str}.md"
    generate_report(queries, pages, posts, analysis, report_path)

    # Also save raw data for future reference
    raw_data = {
        "date": date_str,
        "gsc_queries": queries,
        "gsc_pages": pages,
        "ghost_posts": [
            {"title": p["title"], "slug": p["slug"], "tags": p["tags"]}
            for p in posts
        ],
        "analysis": analysis,
    }
    raw_path = output_dir / f"seo_data_{date_str}.json"
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"Pipeline complete. Report: {report_path}")
    return report_path
