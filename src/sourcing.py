"""Phase 1 — Sourcing: collect raw news items from RSS, HN, Reddit, GitHub."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from .utils import RateLimiter

logger = logging.getLogger(__name__)

# Shared rate limiter: 2 req/s max across all external sources
_rl = RateLimiter(calls_per_second=0.5)

CUTOFF_DAYS = 7


def _cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)


def _strip_html(html: str, max_len: int = 300) -> str:
    try:
        return BeautifulSoup(html, "lxml").get_text(" ", strip=True)[:max_len]
    except Exception:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)[:max_len]


# ---------------------------------------------------------------------------
# RSS
# ---------------------------------------------------------------------------

def fetch_rss(feeds: list[dict]) -> list[dict]:
    items: list[dict] = []
    cutoff = _cutoff()

    for feed_cfg in feeds:
        url = feed_cfg["url"]
        name = feed_cfg["name"]
        try:
            parsed = feedparser.parse(url, request_headers={"User-Agent": "devai-newsletter/1.0"})
            count = 0
            for entry in parsed.entries:
                # Resolve publish date
                pub: datetime | None = None
                for attr in ("published_parsed", "updated_parsed"):
                    ts = getattr(entry, attr, None)
                    if ts:
                        try:
                            pub = datetime(*ts[:6], tzinfo=timezone.utc)
                        except Exception:
                            pass
                        break

                if pub and pub < cutoff:
                    continue

                # Resolve snippet
                snippet = ""
                for attr in ("summary", "description"):
                    raw = getattr(entry, attr, None)
                    if raw:
                        snippet = _strip_html(str(raw))
                        break
                if not snippet:
                    content_list = getattr(entry, "content", [])
                    if content_list:
                        snippet = _strip_html(content_list[0].get("value", ""))

                link = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                if not link or not title:
                    continue

                items.append({
                    "title": title,
                    "url": link,
                    "source": name,
                    "published": pub.isoformat() if pub else None,
                    "snippet": snippet,
                    "type": "rss",
                })
                count += 1

            logger.info(f"RSS {name}: {count} items (last 7d)")
        except Exception as exc:
            logger.warning(f"RSS {name} ({url}) failed: {exc}")

    return items


# ---------------------------------------------------------------------------
# Hacker News (Algolia Search API)
# ---------------------------------------------------------------------------

def fetch_hackernews(keywords: list[str], min_score: int) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    cutoff_ts = int(_cutoff().timestamp())

    for kw in keywords:
        _rl.wait()
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    "https://hn.algolia.com/api/v1/search",
                    params={
                        "query": kw,
                        "tags": "story",
                        "numericFilters": f"points>={min_score},created_at_i>{cutoff_ts}",
                        "hitsPerPage": 20,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            for hit in data.get("hits", []):
                hn_id = str(hit.get("objectID", ""))
                if hn_id in seen:
                    continue
                seen.add(hn_id)

                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hn_id}"
                items.append({
                    "title": hit.get("title", "").strip(),
                    "url": story_url,
                    "source": "Hacker News",
                    "published": hit.get("created_at"),
                    "snippet": (
                        f"Score: {hit.get('points', 0)} pts · "
                        f"{hit.get('num_comments', 0)} comments"
                    ),
                    "type": "hackernews",
                })

            logger.debug(f"HN '{kw}': {len(data.get('hits', []))} hits")
        except Exception as exc:
            logger.warning(f"HN keyword '{kw}' failed: {exc}")

    logger.info(f"HN total: {len(items)} unique stories")
    return items


# ---------------------------------------------------------------------------
# Reddit (public JSON endpoint, no auth)
# ---------------------------------------------------------------------------

def fetch_reddit(
    subreddits: list[str],
    sort: str,
    time_filter: str,
    min_upvotes: int,
) -> list[dict]:
    items: list[dict] = []
    headers = {
        "User-Agent": "devai-newsletter:v1.0 (automated newsletter aggregator; contact: devai@example.com)"
    }

    for sub in subreddits:
        _rl.wait()
        try:
            with httpx.Client(
                timeout=20, headers=headers, follow_redirects=True
            ) as client:
                resp = client.get(
                    f"https://www.reddit.com/r/{sub}/{sort}.json",
                    params={"t": time_filter, "limit": 25},
                )
                resp.raise_for_status()
                data = resp.json()

            count = 0
            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                if p.get("score", 0) < min_upvotes:
                    continue
                if p.get("removed_by_category"):
                    continue

                # For self-posts without content, skip (low value)
                selftext = (p.get("selftext") or "").strip()
                if p.get("is_self") and not selftext:
                    continue

                # Prefer external URL; fall back to Reddit thread
                url = p.get("url", "")
                if not url or "reddit.com/r/" in url or url.endswith("/"):
                    url = f"https://reddit.com{p.get('permalink', '')}"

                snippet = selftext[:280] if selftext else (
                    f"Score: {p.get('score', 0)} · {p.get('num_comments', 0)} comments"
                )

                items.append({
                    "title": p.get("title", "").strip(),
                    "url": url,
                    "source": f"r/{sub}",
                    "published": datetime.fromtimestamp(
                        float(p.get("created_utc", 0)), tz=timezone.utc
                    ).isoformat(),
                    "snippet": snippet,
                    "type": "reddit",
                })
                count += 1

            logger.info(f"Reddit r/{sub}: {count} qualifying posts")
        except Exception as exc:
            logger.warning(f"Reddit r/{sub} failed: {exc}")

    return items


# ---------------------------------------------------------------------------
# GitHub (Search API — no auth, rate-limited at 10 req/min unauthenticated)
# ---------------------------------------------------------------------------

def fetch_github_trending(topics: list[str]) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    cutoff_date = _cutoff().strftime("%Y-%m-%d")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for topic in topics:
        _rl.wait()
        try:
            with httpx.Client(timeout=20, headers=headers) as client:
                resp = client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"topic:{topic} pushed:>{cutoff_date}",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 10,
                    },
                )
                # Respect rate-limit headers
                if resp.status_code == 403:
                    logger.warning(f"GitHub rate limit hit for topic '{topic}', skipping")
                    continue
                resp.raise_for_status()
                data = resp.json()

            for repo in data.get("items", []):
                full_name = repo.get("full_name", "")
                if full_name in seen:
                    continue
                seen.add(full_name)

                desc = (repo.get("description") or "").strip()
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language") or "N/A"

                items.append({
                    "title": f"{repo.get('name', '')} — {desc[:80]}",
                    "url": repo.get("html_url", ""),
                    "source": "GitHub Trending",
                    "published": repo.get("pushed_at"),
                    "snippet": f"★ {stars} stars · {lang} · {desc}",
                    "type": "github",
                    "stars": stars,
                    "language": lang,
                    "full_name": full_name,
                    "description": desc,
                })

            logger.debug(f"GitHub topic '{topic}': {len(data.get('items', []))} repos")
        except Exception as exc:
            logger.warning(f"GitHub topic '{topic}' failed: {exc}")

    logger.info(f"GitHub total: {len(items)} unique repos")
    return items


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    try:
        p = urlparse(url.lower().rstrip("/"))
        return f"{p.netloc}{p.path}"
    except Exception:
        return url.lower().strip()


def deduplicate(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        key = _normalize_url(item.get("url", ""))
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Phase entry point
# ---------------------------------------------------------------------------

def run(config: dict, data_dir: Path, date_str: str) -> Path:
    output = data_dir / f"raw_items_{date_str}.json"

    if output.exists():
        logger.info(f"Sourcing: {output.name} already exists — skipping (idempotent)")
        return output

    all_items: list[dict] = []
    sources = config.get("sources", {})

    if "rss" in sources:
        all_items.extend(fetch_rss(sources["rss"]))

    if "hackernews" in sources:
        hn = sources["hackernews"]
        all_items.extend(
            fetch_hackernews(hn.get("keywords", []), hn.get("min_score", 50))
        )

    if "reddit" in sources:
        rd = sources["reddit"]
        all_items.extend(
            fetch_reddit(
                rd.get("subreddits", []),
                rd.get("sort", "top"),
                rd.get("time", "week"),
                rd.get("min_upvotes", 100),
            )
        )

    if "github_trending" in sources:
        gh = sources["github_trending"]
        all_items.extend(fetch_github_trending(gh.get("topics", [])))

    unique = deduplicate(all_items)
    logger.info(
        f"Sourcing complete: {len(unique)} unique items "
        f"(from {len(all_items)} raw across all sources)"
    )

    output.write_text(
        json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"Saved → {output}")
    return output
