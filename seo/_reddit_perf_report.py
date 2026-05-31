"""One-shot performance report for Khavel_dev comments.
Uses the authenticated Playwright session to bypass the unauth 403 on .json.
Fetches about.json, the user's comments.json, and per-comment threads to
read replies. Writes JSON to .reddit-perf-out.json and prints a summary.
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reddit_session import sync_playwright, PROFILE_DIR

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "reddit_comment_log.jsonl"
OUT_FILE = SCRIPT_DIR / ".reddit-perf-out.json"


def page_fetch_json(page, url):
    return page.evaluate("""(url) => {
        return fetch(url, {credentials: 'same-origin', headers: {'Accept':'application/json'}})
            .then(r => r.json())
            .then(d => ({ok: true, data: d}))
            .catch(e => ({ok: false, error: e.message}));
    }""", url)


def load_log():
    rows = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def find_comment(children, target):
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        if d.get("name") == target or ("t1_" + d.get("id", "")) == target:
            return d
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            r = find_comment(replies["data"]["children"], target)
            if r:
                return r
    return None


def collect_replies(comment_data):
    """Return list of {author, body, score} for direct + nested replies."""
    out = []
    replies = comment_data.get("replies")
    if isinstance(replies, dict):
        for ch in replies["data"]["children"]:
            if ch.get("kind") != "t1":
                continue
            d = ch["data"]
            out.append({
                "author": d.get("author"),
                "body": d.get("body"),
                "score": d.get("score"),
            })
            out.extend(collect_replies(d))
    return out


def main():
    rows = load_log()
    out = {"about": None, "user_comments": [], "perf": []}

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

        # --- about.json ---
        res = page_fetch_json(page, "https://old.reddit.com/user/Khavel_dev/about.json?raw_json=1")
        if res.get("ok"):
            d = res["data"].get("data", {})
            out["about"] = {
                "comment_karma": d.get("comment_karma"),
                "link_karma": d.get("link_karma"),
                "total_karma": d.get("total_karma"),
                "created_utc": d.get("created_utc"),
                "is_suspended": d.get("is_suspended"),
                "verified": d.get("verified"),
                "has_verified_email": d.get("has_verified_email"),
                "name": d.get("name"),
            }
        else:
            out["about"] = {"error": res.get("error")}
        time.sleep(1.5)

        # --- user comments.json (public visibility + scores) ---
        res = page_fetch_json(page, "https://old.reddit.com/user/Khavel_dev/comments.json?limit=100&raw_json=1")
        ucby_id = {}
        if res.get("ok"):
            try:
                for ch in res["data"]["data"]["children"]:
                    d = ch["data"]
                    rec = {
                        "id": "t1_" + d.get("id", ""),
                        "score": d.get("score"),
                        "subreddit": d.get("subreddit"),
                        "body": (d.get("body") or "")[:120],
                        "permalink": d.get("permalink"),
                        "num_replies_indicator": d.get("num_comments"),
                        "created_utc": d.get("created_utc"),
                        "controversiality": d.get("controversiality"),
                    }
                    out["user_comments"].append(rec)
                    ucby_id[rec["id"]] = rec
            except Exception as e:
                out["user_comments"] = [{"error": str(e)}]
        else:
            out["user_comments"] = [{"error": res.get("error")}]
        time.sleep(1.5)

        # --- per-comment thread fetch for scores + replies ---
        for row in rows:
            post_id = row["post_id"]
            cid = row["comment_id"]
            sub = row["subreddit"]
            url = f"https://old.reddit.com/r/{sub}/comments/{post_id}.json?limit=500&raw_json=1"
            res = page_fetch_json(page, url)
            entry = {
                "date": row.get("date"),
                "sub": sub,
                "topic": row.get("topic"),
                "post_id": post_id,
                "cid": cid,
            }
            try:
                comments = res["data"][1]["data"]["children"]
                found = find_comment(comments, cid)
                if found:
                    reps = collect_replies(found)
                    entry.update({
                        "found": True,
                        "score": found.get("score"),
                        "num_replies": len(reps),
                        "removed": found.get("body") in ("[removed]", "[deleted]"),
                        "replies": reps,
                    })
                else:
                    # fall back to score from user comments listing
                    uc = ucby_id.get(cid)
                    entry.update({"found": False, "score_from_userlist": uc.get("score") if uc else None})
            except Exception as e:
                entry.update({"error": str(e)})
            out["perf"].append(entry)
            time.sleep(1.5)

        ctx.close()

    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    print("ABOUT:", json.dumps(out["about"], ensure_ascii=False))
    print("USER_COMMENTS_COUNT:", len([c for c in out["user_comments"] if "id" in c]))
    for e in out["perf"]:
        print("PERF", e.get("date"), e.get("sub"),
              "score=", e.get("score", e.get("score_from_userlist")),
              "replies=", e.get("num_replies"),
              "found=", e.get("found"), e.get("error", ""))


if __name__ == "__main__":
    main()
