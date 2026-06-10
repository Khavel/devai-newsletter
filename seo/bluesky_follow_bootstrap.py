"""One-time follow bootstrap for the product Bluesky accounts.

Usage:
  python bluesky_follow_bootstrap.py --account Sharpyard --dry-run   # show candidates
  python bluesky_follow_bootstrap.py --account Sharpyard             # follow them
  python bluesky_follow_bootstrap.py --all [--dry-run]

Searches the public API per niche term, keeps credible accounts (display name +
bio present, followers >= MIN_FOLLOWERS), dedupes, caps at MAX_FOLLOWS per
account, then follows via the authenticated client. Never follows our own
accounts. Logs followed handles to bluesky_follow_log.jsonl.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx

from bluesky_post import ACCOUNTS, load_env, get_credentials  # reuse, do not fork

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "bluesky_follow_log.jsonl"
SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"

MIN_FOLLOWERS = 200
MAX_FOLLOWS = 12

OWN_HANDLES = {
    "sharpyard.bsky.social", "devaisemanal.bsky.social",
    "futprob.bsky.social", "statlinenerd.bsky.social",
}

# Niche search terms per account (ICP-aligned communities).
SEARCH_TERMS = {
    "Sharpyard": [".NET developer", "csharp", "dotnet", "build in public SaaS", "indie hacker developer"],
    "DevAISemanal": ["desarrollador web", "programacion", "desarrollo software espanol",
                     "inteligencia artificial espanol", "javascript espanol", "midudev"],
    "FutProbLab": ["soccer analytics", "expected goals", "football data analyst", "futbol datos"],
    "StatLineNerd": ["NBA analytics", "basketball stats", "NBA data", "WNBA stats"],
}

# Hand-curated exclusions (wrong niche or unsuitable despite matching a term).
EXCLUDE = {
    "dotnet.dog",            # NSFW account, only nominally dotnet
    "aaronschatz.com",       # NFL (American football), wrong sport for FutPicks
    "cfbnumbers.bsky.social",  # college (American) football
    "sportsmedanalytics.bsky.social",  # NFL injury analytics, wrong sport
    "numax.org",             # cinema/bookshop, matched a broad ES term
    "rickysanta.bsky.social",  # political account, not dev
    "akenaton86.bsky.social",  # generic gamer, weak dev fit
}


def search_candidates(account: str) -> list[dict]:
    seen, out = set(), []
    for term in SEARCH_TERMS[account]:
        try:
            r = httpx.get(SEARCH_URL, params={"q": term, "limit": 25}, timeout=20)
            actors = r.json().get("actors", []) if r.status_code == 200 else []
        except Exception:
            actors = []
        for a in actors:
            handle = a.get("handle", "")
            if handle in seen or handle in OWN_HANDLES or handle in EXCLUDE:
                continue
            seen.add(handle)
            # searchActors returns limited fields; fetch profile for follower count
            try:
                p = httpx.get(
                    "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile",
                    params={"actor": handle}, timeout=15).json()
            except Exception:
                continue
            if not (p.get("displayName") and p.get("description")):
                continue
            if (p.get("followersCount") or 0) < MIN_FOLLOWERS:
                continue
            out.append({
                "handle": handle, "did": p["did"],
                "name": p["displayName"], "followers": p["followersCount"],
                "bio": (p.get("description") or "").replace("\n", " ")[:90],
                "term": term,
            })
    out.sort(key=lambda c: -c["followers"])
    return out[:MAX_FOLLOWS]


def bootstrap(account: str, dry_run: bool) -> bool:
    cands = search_candidates(account)
    if not cands:
        print(f"{account}: no candidates found")
        return False
    print(f"\n== {account}: {len(cands)} candidates ==")
    for c in cands:
        print(f"  @{c['handle']:38} {c['followers']:>7} followers | {c['name'][:28]:28} | {c['bio'][:60]}")
    if dry_run:
        return True

    from atproto import Client
    handle, app_password = get_credentials(account)
    client = Client()
    client.login(handle, app_password)
    followed = []
    for c in cands:
        try:
            client.follow(c["did"])
            followed.append(c["handle"])
        except Exception as e:
            print(f"  follow failed @{c['handle']}: {e}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "account": account, "followed": followed,
        }, ensure_ascii=False) + "\n")
    print(f"  -> followed {len(followed)}/{len(cands)}; logged to {LOG_FILE.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bootstrap follows for product Bluesky accounts")
    parser.add_argument("--account", choices=list(SEARCH_TERMS.keys()))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = list(SEARCH_TERMS.keys()) if args.all else ([args.account] if args.account else [])
    if not targets:
        parser.error("provide --account <name> or --all")
    if not args.dry_run:
        load_env()
    ok = all(bootstrap(a, args.dry_run) for a in targets)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
