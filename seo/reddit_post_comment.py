"""Post a Reddit comment using text from a file. Auto-logs to reddit_comment_log.jsonl."""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Reuse the hub's reddit account registry (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import reddit_accounts  # type: ignore
except Exception:
    reddit_accounts = None

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "reddit_comment_log.jsonl"
_FALLBACK_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")


def main():
    parser = argparse.ArgumentParser(description="Post a Reddit comment from a text file")
    parser.add_argument("post_id", help="Reddit post ID (e.g., 1to03iw)")
    parser.add_argument("text_file", help="Path to file containing comment text")
    parser.add_argument("--subreddit", "-s", default="", help="Subreddit name for logging")
    parser.add_argument("--topic", "-t", default="", help="Brief topic description for logging")
    parser.add_argument("--parent", "-p", default="", help="Parent comment ID for replies (t1_xxx)")
    parser.add_argument("--account", default=None, help="Reddit persona (default Khavel_dev)")
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8").strip()
    if not text:
        print("ERROR: Comment text file is empty")
        sys.exit(1)

    from reddit_session import sync_playwright, _reddit_api

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if reddit_accounts:
        acct = reddit_accounts.resolve_account(args.account)
        profile_dir = acct["profile_dir"]
        user_agent = acct["user_agent"]
    else:
        profile_dir = str(SCRIPT_DIR / ".reddit-profile")
        user_agent = _FALLBACK_UA

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=user_agent,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        if args.parent:
            thing_id = args.parent if args.parent.startswith("t1_") else f"t1_{args.parent}"
        else:
            thing_id = args.post_id if args.post_id.startswith("t3_") else f"t3_{args.post_id}"

        result = _reddit_api(page, "comment", {"thing_id": thing_id, "text": text})

        if result.get("ok"):
            things = result.get("data", {}).get("things", [])
            cid = things[0]["data"]["id"] if things else "?"
            print(f"OK: Comment posted (id: {cid})")

            log_entry = {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "post_id": args.post_id,
                "comment_id": cid,
                "subreddit": args.subreddit,
                "topic": args.topic,
                "parent": args.parent or "",
                "text_preview": text[:80],
            }
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            print(f"Logged to {LOG_FILE}")
        else:
            err = result.get("error", "unknown")
            print(f"ERROR: {err}")
            sys.exit(1)

        ctx.close()


if __name__ == "__main__":
    main()
