"""One-shot browse helper: fetch listings + check prior comments via the
authenticated Playwright session (bypasses the unauth 403 on .json)."""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reddit_session import sync_playwright, PROFILE_DIR

SCRIPT_DIR = Path(__file__).parent
OUT_FILE = SCRIPT_DIR / ".reddit-browse-out.json"

# subs to browse (target + week-1 diversity)
TARGET_SUBS = ["ClaudeAI", "microsaas", "SideProject"]
DIVERSITY_SUBS = ["Python", "webdev"]

# yesterday's comments to verify: (sub, post_id, comment_fullname)
PERF_CHECKS = [
    ("ClaudeAI", "1trrzb8", "t1_ooq7cgb"),
    ("microsaas", "1trrvu8", "t1_ooq7nl0"),
    ("Python", "1tromoz", "t1_ooq7x2h"),
]


def page_fetch_json(page, url):
    """Fetch a .json URL from the authenticated page context."""
    return page.evaluate("""(url) => {
        return fetch(url, {credentials: 'same-origin', headers: {'Accept':'application/json'}})
            .then(r => r.json())
            .then(d => ({ok: true, data: d}))
            .catch(e => ({ok: false, error: e.message}));
    }""", url)


def find_comment(children, target):
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        if d.get("name") == target:
            return d
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            r = find_comment(replies["data"]["children"], target)
            if r:
                return r
    return None


def main():
    out = {"listings": {}, "perf": []}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # --- Performance checks for yesterday's comments ---
        for sub, post_id, cid in PERF_CHECKS:
            url = f"https://old.reddit.com/r/{sub}/comments/{post_id}.json?limit=200&raw_json=1"
            res = page_fetch_json(page, url)
            entry = {"sub": sub, "post_id": post_id, "cid": cid}
            try:
                comments = res["data"][1]["data"]["children"]
                found = find_comment(comments, cid)
                if found:
                    reps = found.get("replies")
                    nrep = len(reps["data"]["children"]) if isinstance(reps, dict) else 0
                    entry.update({
                        "found": True,
                        "score": found.get("score"),
                        "replies": nrep,
                        "removed": found.get("body") in ("[removed]", "[deleted]"),
                    })
                else:
                    entry.update({"found": False})
            except Exception as e:
                entry.update({"error": str(e)})
            out["perf"].append(entry)
            time.sleep(1.5)

        # --- Listings ---
        for sub in TARGET_SUBS + DIVERSITY_SUBS:
            posts = []
            for sort, lim in [("hot", 15), ("new", 10)]:
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

    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    # quick perf summary to stdout
    for e in out["perf"]:
        print("PERF", e)


if __name__ == "__main__":
    main()
