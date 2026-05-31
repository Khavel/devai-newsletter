"""
Persistent Twitter/X browser session using Playwright.
Each account gets its own browser profile directory.

Usage:
  python twitter_session.py --account DevAISemanal             # Interactive session
  python twitter_session.py --account DevAISemanal --login      # Login flow
  python twitter_session.py --account DevAISemanal --cmd "tweet Hello world"
"""

import argparse
import json
import os
import re
import sys
import time
import random
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "twitter_post_log.jsonl"
RESULT_FILE = SCRIPT_DIR / ".twitter-result.txt"
DRAFT_FILE = SCRIPT_DIR / ".twitter-draft.txt"

# Account configs — profile dirs are per-account
ACCOUNTS = {
    "DevAISemanal": {
        "handle": "@DevAISemanal",
        "profile_dir": str(SCRIPT_DIR / ".twitter-profile-devai"),
        "product": "DevAI Semanal",
    },
    "StatLineNerd": {
        "handle": "@StatLineNerd",
        "profile_dir": str(SCRIPT_DIR / ".twitter-profile-statline"),
        "product": "NbaPropLab",
    },
    "FutProbLab": {
        "handle": "@FutProbLab",
        "profile_dir": str(SCRIPT_DIR / ".twitter-profile-futprob"),
        "product": "FutPicks",
    },
}

# Rotate user agents across accounts
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

VIEWPORTS = [
    {"width": 1280, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
]


def _human_delay(lo=1.5, hi=3.5):
    time.sleep(random.uniform(lo, hi))


def _get_account_config(account_name):
    if account_name not in ACCOUNTS:
        print(f"ERROR: Unknown account '{account_name}'. Known: {list(ACCOUNTS.keys())}")
        sys.exit(1)
    return ACCOUNTS[account_name]


def _launch_browser(pw, account_name):
    """Launch persistent browser for the given account."""
    config = _get_account_config(account_name)
    idx = list(ACCOUNTS.keys()).index(account_name)

    ctx = pw.chromium.launch_persistent_context(
        config["profile_dir"],
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--disable-infobars",
        ],
        user_agent=USER_AGENTS[idx % len(USER_AGENTS)],
        viewport=VIEWPORTS[idx % len(VIEWPORTS)],
        locale="en-US",
        timezone_id="America/Chicago",
    )
    return ctx


def is_logged_in(page):
    """Check if logged into Twitter/X by looking for compose tweet elements."""
    try:
        # On x.com home, logged-in users see the compose area or nav items
        # Check for the "Post" or navigation sidebar items
        nav = page.locator('nav[aria-label="Primary"]')
        if nav.count() > 0:
            return True
        # Also check for the tweet compose button
        compose = page.locator('a[aria-label="Post"], a[data-testid="SideNav_NewTweet_Button"]')
        if compose.count() > 0:
            return True
        # Check for profile link in sidebar
        profile = page.locator('a[data-testid="AppTabBar_Profile_Link"]')
        if profile.count() > 0:
            return True
        return False
    except Exception:
        return False


def do_login(page, ctx, account_name, timeout=180):
    """Navigate to login page and wait for manual login."""
    config = _get_account_config(account_name)
    print(f"Logging in as {config['handle']}...")
    print(f"  Please log in manually in the browser window.")
    print(f"  The browser profile will be saved to: {config['profile_dir']}")

    page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    # Wait for manual login — Twitter has aggressive bot detection,
    # automated form filling is risky. Manual login is safer.
    print(f"  Waiting up to {timeout}s for login...")
    for i in range(timeout // 5):
        time.sleep(5)
        try:
            # Check if we've been redirected to the home feed
            if "home" in page.url.lower() or page.url == "https://x.com/":
                if is_logged_in(page):
                    print("  Login successful!")
                    return True
        except Exception:
            pass
        if (i + 1) % 6 == 0:
            print(f"  Still waiting... ({(i+1)*5}s)")

    return False


def _get_ct0(page):
    """Get the ct0 CSRF token from cookies — needed for API calls."""
    cookies = page.context.cookies()
    for c in cookies:
        if c["name"] == "ct0":
            return c["value"]
    return None


def _get_auth_token(page):
    """Get auth_token from cookies to verify login state."""
    cookies = page.context.cookies()
    for c in cookies:
        if c["name"] == "auth_token":
            return c["value"]
    return None


def _twitter_api(page, method, endpoint, payload=None):
    """Call Twitter's internal GraphQL/API from the page context."""
    return page.evaluate("""(args) => {
        const [method, endpoint, payload] = args;
        return new Promise((resolve) => {
            // Get ct0 from cookie
            const ct0 = document.cookie.split(';')
                .map(c => c.trim())
                .find(c => c.startsWith('ct0='));
            const csrfToken = ct0 ? ct0.split('=')[1] : '';

            if (!csrfToken) {
                resolve({ok: false, error: 'no_csrf_token'});
                return;
            }

            const headers = {
                'Content-Type': 'application/json',
                'x-csrf-token': csrfToken,
                'x-twitter-auth-type': 'OAuth2Session',
                'x-twitter-active-user': 'yes',
                'x-twitter-client-language': 'en',
            };

            const opts = {
                method: method,
                headers: headers,
                credentials: 'same-origin',
            };
            if (payload) {
                opts.body = JSON.stringify(payload);
            }

            fetch('https://x.com' + endpoint, opts)
                .then(r => r.json())
                .then(data => {
                    if (data.errors) {
                        resolve({ok: false, error: JSON.stringify(data.errors)});
                    } else {
                        resolve({ok: true, data: data});
                    }
                })
                .catch(e => resolve({ok: false, error: e.message}));
        });
    }""", [method, endpoint, payload])


def do_tweet(page, text, account_name):
    """Post a tweet using Twitter's internal CreateTweet GraphQL mutation."""
    print(f"Tweeting as {ACCOUNTS[account_name]['handle']}...")

    # Twitter's CreateTweet GraphQL endpoint
    payload = {
        "variables": {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False,
            },
            "semantic_annotation_ids": [],
        },
        "features": {
            "communities_web_enable_tweet_community_results_fetch": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "articles_preview_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
        },
        "queryId": "znq7jUAqRjmPj7IszLem5Q",
    }

    result = _twitter_api(
        page,
        "POST",
        "/i/api/graphql/znq7jUAqRjmPj7IszLem5Q/CreateTweet",
        payload,
    )

    if result and result.get("ok"):
        tweet_data = result.get("data", {})
        # Try to extract tweet ID from response
        try:
            tweet_result = tweet_data.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result", {})
            tweet_id = tweet_result.get("rest_id", "?")
        except Exception:
            tweet_id = "?"
        print(f"  Tweet posted (id: {tweet_id})")
        _log_post(account_name, "tweet", text, tweet_id)
        return {"ok": True, "tweet_id": tweet_id}
    else:
        err = result.get("error", "unknown") if result else "null response"
        print(f"  ERROR: {err}")
        return {"ok": False, "error": err}


def do_tweet_ui(page, text, account_name):
    """Post a tweet via the UI (fallback if GraphQL doesn't work).
    This is slower but more reliable as it doesn't depend on internal API stability."""
    print(f"Tweeting via UI as {ACCOUNTS[account_name]['handle']}...")

    # Navigate to home to get the compose box
    if "home" not in page.url:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)

    # Click the compose area
    compose = page.locator('div[data-testid="tweetTextarea_0"]')
    if compose.count() == 0:
        # Try clicking the "Post" button in sidebar to open compose
        post_btn = page.locator('a[data-testid="SideNav_NewTweet_Button"]')
        if post_btn.count() > 0:
            post_btn.first.click()
            time.sleep(2)
            compose = page.locator('div[data-testid="tweetTextarea_0"]')

    if compose.count() == 0:
        return {"ok": False, "error": "Could not find compose textarea"}

    compose.first.click()
    _human_delay(0.5, 1.0)

    # Type the text with human-like speed
    page.keyboard.type(text, delay=random.randint(20, 60))
    _human_delay(1.0, 2.0)

    # Click the Post button
    post_btn = page.locator('button[data-testid="tweetButton"], button[data-testid="tweetButtonInline"]')
    if post_btn.count() == 0:
        return {"ok": False, "error": "Could not find Post button"}

    post_btn.first.click()
    time.sleep(3)

    print("  Tweet posted via UI")
    _log_post(account_name, "tweet", text, "ui-post")
    return {"ok": True, "tweet_id": "ui-post"}


def do_reply(page, tweet_url, text, account_name):
    """Reply to a tweet by navigating to it and using the reply compose."""
    print(f"Replying to {tweet_url}...")

    page.goto(tweet_url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(4)

    # Find the reply compose area
    reply_box = page.locator('div[data-testid="tweetTextarea_0"]')
    if reply_box.count() == 0:
        return {"ok": False, "error": "Could not find reply textarea"}

    reply_box.first.click()
    _human_delay(0.5, 1.0)
    page.keyboard.type(text, delay=random.randint(20, 60))
    _human_delay(1.0, 2.0)

    reply_btn = page.locator('button[data-testid="tweetButton"], button[data-testid="tweetButtonInline"]')
    if reply_btn.count() == 0:
        return {"ok": False, "error": "Could not find Reply button"}

    reply_btn.first.click()
    time.sleep(3)

    _log_post(account_name, "reply", text, f"reply-to-{tweet_url}")
    return {"ok": True}


def do_like(page, tweet_url, account_name):
    """Like a tweet by navigating to it and clicking the like button."""
    print(f"Liking {tweet_url}...")

    page.goto(tweet_url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)

    like_btn = page.locator('button[data-testid="like"]')
    if like_btn.count() == 0:
        # Might already be liked
        unlike_btn = page.locator('button[data-testid="unlike"]')
        if unlike_btn.count() > 0:
            return {"ok": True, "note": "already liked"}
        return {"ok": False, "error": "Could not find like button"}

    like_btn.first.click()
    time.sleep(1)
    return {"ok": True}


def do_retweet(page, tweet_url, account_name):
    """Retweet a tweet."""
    print(f"Retweeting {tweet_url}...")

    page.goto(tweet_url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)

    rt_btn = page.locator('button[data-testid="retweet"]')
    if rt_btn.count() == 0:
        return {"ok": False, "error": "Could not find retweet button"}

    rt_btn.first.click()
    time.sleep(1)

    # Confirm retweet in the popup
    confirm = page.locator('div[data-testid="retweetConfirm"]')
    if confirm.count() > 0:
        confirm.first.click()
        time.sleep(1)

    return {"ok": True}


def _log_post(account_name, action, text, tweet_id):
    """Log a tweet/reply/like to the JSONL log."""
    config = ACCOUNTS[account_name]
    entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "account": account_name,
        "handle": config["handle"],
        "product": config["product"],
        "action": action,
        "tweet_id": str(tweet_id),
        "text_preview": text[:120],
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Logged to {LOG_FILE}")


def run_command(page, cmd_str, account_name):
    """Parse and execute a command string."""
    parts = cmd_str.strip().split(maxsplit=1)
    if not parts:
        return "ERROR: Empty command"

    action = parts[0].lower()

    if action == "tweet" and len(parts) > 1:
        result = do_tweet(page, parts[1], account_name)
        if not result.get("ok"):
            # Fallback to UI method
            print("  GraphQL failed, trying UI method...")
            result = do_tweet_ui(page, parts[1], account_name)
        return f"OK: {result}" if result.get("ok") else f"ERROR: {result}"

    elif action == "tweet_ui" and len(parts) > 1:
        result = do_tweet_ui(page, parts[1], account_name)
        return f"OK: {result}" if result.get("ok") else f"ERROR: {result}"

    elif action == "reply" and len(parts) > 1:
        rest = parts[1].split(maxsplit=1)
        if len(rest) == 2:
            result = do_reply(page, rest[0], rest[1], account_name)
            return f"OK: {result}" if result.get("ok") else f"ERROR: {result}"
        return "ERROR: Usage: reply <tweet_url> <text>"

    elif action == "like" and len(parts) > 1:
        result = do_like(page, parts[1].strip(), account_name)
        return f"OK: {result}" if result.get("ok") else f"ERROR: {result}"

    elif action == "retweet" and len(parts) > 1:
        result = do_retweet(page, parts[1].strip(), account_name)
        return f"OK: {result}" if result.get("ok") else f"ERROR: {result}"

    elif action == "screenshot":
        path = SCRIPT_DIR / f"twitter_current_{account_name}.png"
        page.screenshot(path=str(path))
        return f"OK: Screenshot saved to {path}"

    elif action == "status":
        logged = is_logged_in(page)
        ct0 = _get_ct0(page)
        auth = _get_auth_token(page)
        return f"OK: logged_in={logged} ct0={'yes' if ct0 else 'no'} auth={'yes' if auth else 'no'} url={page.url}"

    elif action == "goto" and len(parts) > 1:
        page.goto(parts[1].strip(), wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        return f"OK: Navigated to {page.url}"

    else:
        return f"ERROR: Unknown command: {action}. Available: tweet, tweet_ui, reply, like, retweet, screenshot, status, goto"


def main():
    parser = argparse.ArgumentParser(description="Twitter/X Playwright session")
    parser.add_argument("--account", "-a", required=True,
                        choices=list(ACCOUNTS.keys()),
                        help="Account to use")
    parser.add_argument("--cmd", help="Single command to execute then exit")
    parser.add_argument("--login", action="store_true", help="Run login flow")
    parser.add_argument("--wait", type=int, default=180, help="Login wait timeout")
    args = parser.parse_args()

    config = _get_account_config(args.account)
    print(f"Starting Twitter session for {config['handle']} ({config['product']})...")
    print(f"  Profile dir: {config['profile_dir']}")

    pw = sync_playwright().start()
    ctx = _launch_browser(pw, args.account)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    if args.login:
        success = do_login(page, ctx, args.account, args.wait)
        if success:
            print("Login complete! Profile saved.")
        else:
            print("Login timed out.")
        ctx.close()
        pw.stop()
        return

    # Check if already logged in
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    if not is_logged_in(page):
        print("Not logged in. Run with --login first:")
        print(f"  python twitter_session.py --account {args.account} --login")
        ctx.close()
        pw.stop()
        return

    print(f"Logged in as {config['handle']}!")

    if args.cmd:
        result = run_command(page, args.cmd, args.account)
        print(result)
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        cmd_file = SCRIPT_DIR / ".twitter-cmd.txt"
        print(f"\nSession active. Write commands to {cmd_file}")
        print("Commands: tweet <text> | reply <url> <text> | like <url> | retweet <url> | screenshot | status")
        print("Write 'quit' to exit.\n")

        while True:
            if cmd_file.exists():
                cmd = cmd_file.read_text(encoding="utf-8").strip()
                cmd_file.unlink()

                if cmd.lower() == "quit":
                    print("Quitting...")
                    break

                result = run_command(page, cmd, args.account)
                print(result)
                with open(RESULT_FILE, "w", encoding="utf-8") as f:
                    f.write(result)
            else:
                time.sleep(2)

    ctx.close()
    pw.stop()
    print("Session closed.")


if __name__ == "__main__":
    main()
