"""Account-aware promo research helper: fetch target subs' RULES + top promo-style
posts via the AUTHENTICATED Playwright session (read-only). This is the discovery
step of the Phase 2 transition playbook: before drafting any promotional post, learn
each sub's self-promo rules and what promo formats actually land there.

Usage:
  python _reddit_research_promo.py --account Khavel_dev --subs ClaudeAI,csharp
  python _reddit_research_promo.py --account xGNerd --subs SoccerBetting,FootballTips \\
      --queries "I built,track record,my model"

Writes .reddit-promo-research-<account>.json and prints a per-sub summary
(rule count + search hits). LOGGED_IN check is implicit: if the session is dead the
search fetches return errors, which surface in the JSON.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
# Default promo-discovery queries: how "I shipped a thing" posts are usually phrased.
_DEFAULT_QUERIES = ["I built", "open sourced", "starter kit", "boilerplate", "I made"]


def parse_csv(raw, fallback=None):
    if not raw or not raw.strip():
        return list(fallback or [])
    parts = [s.strip().removeprefix("r/").strip() for s in raw.replace(" ", ",").split(",")
             if s.strip()]
    return parts or list(fallback or [])


def page_fetch_json(page, url):
    return page.evaluate("""(url) => {
        return fetch(url, {credentials: 'same-origin', headers: {'Accept':'application/json'}})
            .then(r => r.json())
            .then(d => ({ok: true, data: d}))
            .catch(e => ({ok: false, error: e.message}));
    }""", url)


def main():
    ap = argparse.ArgumentParser(description="Account-aware authenticated Reddit promo research")
    ap.add_argument("--account", default="Khavel_dev", help="persona (default Khavel_dev)")
    ap.add_argument("--subs", default=None, help="comma/space separated target subs (no r/ needed)")
    ap.add_argument("--queries", default=None,
                    help="comma separated promo-discovery search queries (default: I built,open sourced,...)")
    ap.add_argument("--limit", type=int, default=10, help="search results per query")
    args = ap.parse_args()

    subs = parse_csv(args.subs)
    if not subs:
        print("ERROR: --subs is required (the target promo subs to research).")
        sys.exit(2)
    queries = parse_csv(args.queries, _DEFAULT_QUERIES)

    from reddit_session import sync_playwright
    if reddit_accounts:
        acct = reddit_accounts.resolve_account(args.account)
        profile_dir, username = acct["profile_dir"], acct["username"]
    else:
        from reddit_session import PROFILE_DIR
        profile_dir, username = PROFILE_DIR, args.account

    out = {"account": username, "subs": subs, "queries": queries, "rules": {}, "searches": {}}

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            profile_dir, headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
            user_agent=_UA, viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        for sub in subs:
            res = page_fetch_json(page, f"https://old.reddit.com/r/{sub}/about/rules.json")
            if res.get("ok"):
                rules = (res["data"] or {}).get("rules") or []
                out["rules"][sub] = [
                    {"short_name": r.get("short_name"),
                     "description": (r.get("description") or "")[:600]}
                    for r in rules
                ]
            else:
                out["rules"][sub] = [{"error": res.get("error")}]
            time.sleep(1.2)

        for sub in subs:
            out["searches"][sub] = {}
            for q in queries:
                url = (f"https://old.reddit.com/r/{sub}/search.json?q={q.replace(' ', '+')}"
                       f"&restrict_sr=1&sort=top&t=year&limit={args.limit}&raw_json=1")
                res = page_fetch_json(page, url)
                posts = []
                try:
                    for ch in res["data"]["data"]["children"]:
                        d = ch["data"]
                        posts.append({
                            "id": d.get("id"), "title": d.get("title"),
                            "score": d.get("score"), "num_comments": d.get("num_comments"),
                            "created_utc": d.get("created_utc"), "author": d.get("author"),
                            "is_self": d.get("is_self"), "url": d.get("url"),
                            "selftext": (d.get("selftext") or "")[:1200],
                            "link_flair": d.get("link_flair_text"),
                            "permalink": d.get("permalink"),
                            "upvote_ratio": d.get("upvote_ratio"),
                        })
                except Exception as e:
                    posts = [{"error": str(e)}]
                out["searches"][sub][q] = posts
                time.sleep(1.5)

        ctx.close()

    out_file = SCRIPT_DIR / f".reddit-promo-research-{username}.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    for sub in subs:
        nr = len([r for r in out["rules"].get(sub, []) if not r.get("error")])
        nh = sum(len([p for p in v if not p.get("error")]) for v in out["searches"].get(sub, {}).values())
        print(f"r/{sub}: rules={nr} search_hits={nh}")


if __name__ == "__main__":
    main()
