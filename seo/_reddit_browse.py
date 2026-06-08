"""Account-aware browse helper: report login state + karma and fetch subreddit
listings via the AUTHENTICATED Playwright session (bypasses the unauthenticated
403 on reddit's *.json). A same-origin fetch from inside the logged-in tab carries
the session cookies, so it is not blocked the way a server-side httpx GET is.

Usage:
  python _reddit_browse.py --account xGNerd --subs SoccerBetting,soccer,FantasyPL
  python _reddit_browse.py                       # default Khavel_dev + default subs

Writes .reddit-browse-out-<account>.json and prints:
  ACCOUNT <persona>  LOGGED_IN_AS <name|None>  KARMA <comment>/<link>  AGE <days>
  r/<sub>: <n> posts
LOGGED_IN_AS None means the persona's profile has no live session (needs a headed
first-login: `python reddit_session.py --account <name>`).
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Reuse the hub's reddit account registry (single source of truth) for profile dirs.
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import reddit_accounts  # type: ignore
except Exception:
    reddit_accounts = None

SCRIPT_DIR = Path(__file__).parent
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
_DEFAULT_SUBS = ["ClaudeAI", "microsaas", "Python", "dotnet"]


def parse_subs(raw):
    """Parse a comma/space separated sub list, stripping 'r/' prefixes and blanks.

    Empty/None falls back to the default (Khavel_dev) lane so a no-arg run keeps
    working as the original hardcoded helper did.
    """
    if not raw or not raw.strip():
        return list(_DEFAULT_SUBS)
    parts = [s.strip().removeprefix("r/").strip() for s in raw.replace(" ", ",").split(",")]
    return [p for p in parts if p]


def _age_days(created_utc):
    if not created_utc:
        return None
    created = datetime.fromtimestamp(created_utc, tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - created).days


def page_fetch_json(page, url):
    """Fetch a .json URL from the authenticated page context (same-origin cookies)."""
    return page.evaluate("""(url) => {
        return fetch(url, {credentials: 'same-origin', headers: {'Accept':'application/json'}})
            .then(r => r.json())
            .then(d => ({ok: true, data: d}))
            .catch(e => ({ok: false, error: e.message}));
    }""", url)


def main():
    ap = argparse.ArgumentParser(description="Account-aware authenticated Reddit browse")
    ap.add_argument("--account", default=None, help="persona (default Khavel_dev)")
    ap.add_argument("--subs", default=None, help="comma/space separated subs (no r/ needed)")
    ap.add_argument("--hot", type=int, default=15, help="hot posts per sub")
    ap.add_argument("--new", type=int, default=10, help="new posts per sub")
    args = ap.parse_args()

    subs = parse_subs(args.subs)

    from reddit_session import sync_playwright

    if reddit_accounts:
        acct = reddit_accounts.resolve_account(args.account)
        profile_dir = acct["profile_dir"]
        username = acct["username"]
    else:
        from reddit_session import PROFILE_DIR
        profile_dir = PROFILE_DIR
        username = args.account or "Khavel_dev"

    out = {
        "account": username,
        "logged_in_as": None,
        "comment_karma": None,
        "link_karma": None,
        "age_days": None,
        "listings": {},
    }

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
            user_agent=_UA,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # --- Login + gate (the logged-in user's own karma/age) via /api/me.json ---
        me = page_fetch_json(page, "https://old.reddit.com/api/me.json")
        if me.get("ok"):
            d = (me.get("data") or {}).get("data") or {}
            out["logged_in_as"] = d.get("name")
            out["comment_karma"] = d.get("comment_karma")
            out["link_karma"] = d.get("link_karma")
            out["age_days"] = _age_days(d.get("created_utc"))

        # --- Listings (discovery) ---
        for sub in subs:
            posts = []
            for sort, lim in [("hot", args.hot), ("new", args.new)]:
                url = f"https://old.reddit.com/r/{sub}/{sort}.json?limit={lim}&raw_json=1"
                res = page_fetch_json(page, url)
                try:
                    for ch in res["data"]["data"]["children"]:
                        d = ch["data"]
                        posts.append({
                            "id": d.get("id"),
                            "title": d.get("title"),
                            "selftext": (d.get("selftext") or "")[:2000],
                            "num_comments": d.get("num_comments"),
                            "created_utc": d.get("created_utc"),
                            "score": d.get("score"),
                            "permalink": d.get("permalink"),
                            "link_flair": d.get("link_flair_text"),
                            "over_18": d.get("over_18"),
                            "is_self": d.get("is_self"),
                            "locked": d.get("locked"),
                            "stickied": d.get("stickied"),
                            "sort": sort,
                            "author": d.get("author"),
                        })
                except Exception as e:
                    posts.append({"error": str(e), "sort": sort})
                time.sleep(1.5)
            out["listings"][sub] = posts

        ctx.close()

    out_file = SCRIPT_DIR / f".reddit-browse-out-{username}.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"ACCOUNT {username}  LOGGED_IN_AS {out['logged_in_as']}  "
        f"KARMA {out['comment_karma']}/{out['link_karma']}  AGE {out['age_days']}"
    )
    for sub, posts in out["listings"].items():
        n = sum(1 for x in posts if not x.get("error"))
        print(f"  r/{sub}: {n} posts")
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
