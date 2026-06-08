"""Post a Reddit comment using text from a file. Auto-logs to reddit_comment_log.jsonl.

Also enforces a deterministic anti-detection cadence: before posting it sleeps out the
remainder of a randomized 60-120s gap since THIS account's last logged comment, so spacing
holds even when an agent fires several posts back to back (the prose "wait 60-120s" rule was
unreliable). Bypass with --no-wait; tune with --min-gap / --max-gap.
"""
import argparse
import json
import random
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
try:
    from reddit_log import account_of as _account_of  # type: ignore
except Exception:
    def _account_of(entry, default="Khavel_dev"):
        v = (entry or {}).get("account")
        return v if v else default

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "reddit_comment_log.jsonl"
_FALLBACK_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
MIN_GAP_S = 60.0   # anti-detection: min seconds between comments on one account
MAX_GAP_S = 120.0


def build_log_entry(account, post_id, comment_id, subreddit, topic, parent, text, now=None):
    """Build one reddit_comment_log.jsonl row, stamped with the posting *account*."""
    if now is None:
        now = datetime.now(timezone.utc)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "post_id": post_id,
        "comment_id": comment_id,
        "subreddit": subreddit,
        "topic": topic,
        "parent": parent or "",
        "account": account,
        "text_preview": text[:80],
    }


def _parse_row_dt(entry):
    """Parse a log row's UTC datetime from its date+time fields, or None."""
    d, t = (entry or {}).get("date"), (entry or {}).get("time")
    if not d or not t:
        return None
    try:
        return datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def last_post_dt(entries, account):
    """Latest comment datetime (UTC) for *account* across log *entries*, or None.

    Legacy rows with no ``account`` field count as Khavel_dev (reddit_log.account_of).
    """
    latest = None
    for e in entries or []:
        if not e or _account_of(e) != account:
            continue
        dt = _parse_row_dt(e)
        if dt and (latest is None or dt > latest):
            latest = dt
    return latest


def seconds_to_wait(last_dt, now, target_gap):
    """Seconds to sleep so >= target_gap separates the next post from last_dt."""
    if last_dt is None:
        return 0.0
    return max(0.0, target_gap - (now - last_dt).total_seconds())


def _read_log_entries():
    if not LOG_FILE.exists():
        return []
    rows = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def main():
    parser = argparse.ArgumentParser(description="Post a Reddit comment from a text file")
    parser.add_argument("post_id", help="Reddit post ID (e.g., 1to03iw)")
    parser.add_argument("text_file", help="Path to file containing comment text")
    parser.add_argument("--subreddit", "-s", default="", help="Subreddit name for logging")
    parser.add_argument("--topic", "-t", default="", help="Brief topic description for logging")
    parser.add_argument("--parent", "-p", default="", help="Parent comment ID for replies (t1_xxx)")
    parser.add_argument("--account", default=None, help="Reddit persona (default Khavel_dev)")
    parser.add_argument("--no-wait", action="store_true",
                        help="skip the anti-detection inter-comment cadence wait")
    parser.add_argument("--min-gap", type=float, default=MIN_GAP_S,
                        help="min seconds between comments on one account")
    parser.add_argument("--max-gap", type=float, default=MAX_GAP_S,
                        help="max seconds between comments on one account")
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
        account_name = acct["username"]
    else:
        profile_dir = str(SCRIPT_DIR / ".reddit-profile")
        user_agent = _FALLBACK_UA
        account_name = "Khavel_dev"

    # Deterministic anti-detection cadence: sleep out the remainder of a randomized gap
    # since this account's last logged comment (the prose "wait 60-120s" was unreliable).
    if not args.no_wait:
        last_dt = last_post_dt(_read_log_entries(), account_name)
        target = random.uniform(args.min_gap, args.max_gap)
        wait = seconds_to_wait(last_dt, datetime.now(timezone.utc), target)
        if wait > 0:
            ago = int((datetime.now(timezone.utc) - last_dt).total_seconds())
            print(f"[cadence] last {account_name} comment {ago}s ago; "
                  f"waiting {int(wait)}s (target {int(target)}s) before posting")
            time.sleep(wait)

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

            log_entry = build_log_entry(
                account_name, args.post_id, cid, args.subreddit, args.topic, args.parent, text
            )
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
