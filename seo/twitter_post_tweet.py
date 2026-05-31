"""Post a tweet using text from a file. Auto-logs to twitter_post_log.jsonl.

Usage:
  python twitter_post_tweet.py --account DevAISemanal tweet_draft.txt
  python twitter_post_tweet.py --account StatLineNerd tweet_draft.txt --topic "daily picks"
  python twitter_post_tweet.py --account FutProbLab tweet_draft.txt --reply-to https://x.com/user/status/123
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "twitter_post_log.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Post a tweet from a text file")
    parser.add_argument("text_file", help="Path to file containing tweet text")
    parser.add_argument("--account", "-a", required=True,
                        choices=["DevAISemanal", "StatLineNerd", "FutProbLab"],
                        help="Twitter account to use")
    parser.add_argument("--topic", "-t", default="", help="Brief topic for logging")
    parser.add_argument("--reply-to", default="", help="Tweet URL to reply to")
    parser.add_argument("--method", choices=["graphql", "ui"], default="graphql",
                        help="Posting method (default: graphql, fallback: ui)")
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8").strip()
    if not text:
        print("ERROR: Tweet text file is empty")
        sys.exit(1)

    if len(text) > 280:
        print(f"WARNING: Tweet is {len(text)} chars (max 280). Will be truncated by Twitter.")

    from twitter_session import (
        sync_playwright, ACCOUNTS, _launch_browser,
        is_logged_in, do_tweet, do_tweet_ui, do_reply,
    )

    config = ACCOUNTS[args.account]
    print(f"Posting as {config['handle']} ({config['product']})...")

    pw = sync_playwright().start()
    ctx = _launch_browser(pw, args.account)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    if not is_logged_in(page):
        print(f"ERROR: Not logged in as {config['handle']}. Run login first:")
        print(f"  python twitter_session.py --account {args.account} --login")
        ctx.close()
        pw.stop()
        sys.exit(1)

    print(f"Logged in as {config['handle']}")

    if args.reply_to:
        result = do_reply(page, args.reply_to, text, args.account)
    elif args.method == "ui":
        result = do_tweet_ui(page, text, args.account)
    else:
        result = do_tweet(page, text, args.account)
        if not result.get("ok"):
            print("  GraphQL failed, trying UI fallback...")
            result = do_tweet_ui(page, text, args.account)

    if result.get("ok"):
        print(f"OK: Tweet posted successfully")
        # The logging is handled by do_tweet/do_tweet_ui internally
    else:
        print(f"ERROR: {result.get('error', 'unknown')}")
        sys.exit(1)

    ctx.close()
    pw.stop()


if __name__ == "__main__":
    main()
