"""
Persistent Reddit browser session.
Keeps the browser open and accepts commands via stdin or a command file.

Usage:
  python reddit_session.py                    # Start browser, log in, then accept commands
  python reddit_session.py --cmd "comment 1to763e Hello world"  # Run one command and exit
"""

import argparse
import json
import os
import re
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
import random

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx
from playwright.sync_api import sync_playwright

PROFILE_DIR = str(Path(__file__).parent / ".reddit-profile")
USERNAME = "Khavel_dev"
JSON_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"}
CMD_FILE = str(Path(__file__).parent / ".reddit-cmd.txt")
RESULT_FILE = str(Path(__file__).parent / ".reddit-result.txt")


def _get_json(path, params=None):
    url = f"https://www.reddit.com{path}.json"
    r = httpx.get(url, headers=JSON_HEADERS, params=params or {}, timeout=15, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _human_delay(lo=1.5, hi=3.5):
    time.sleep(random.uniform(lo, hi))


def _dismiss_popups(page):
    """Dismiss cookie banners using Playwright locators (handles shadow DOM)."""
    # Try multiple button texts — Playwright's :has-text works across shadow DOM
    for text in [
        "Reject non-essential", "Rechazar cookies no esenciales",
        "Accept all", "Aceptar todo",
        "Accept", "Aceptar",
        "Refuse", "Rechazar",
    ]:
        try:
            btn = page.locator(f'button:has-text("{text}")')
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=3000)
                print(f"  Dismissed popup: '{text}'")
                time.sleep(1)
                return
        except Exception:
            pass
    # Fallback: try clicking any cookie-related overlay away
    try:
        page.evaluate("""() => {
            // Remove common overlays by class/id patterns
            const overlays = document.querySelectorAll('[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"]');
            overlays.forEach(el => el.remove());
        }""")
    except Exception:
        pass


def do_login(page, ctx, timeout=180):
    """Attempt automated login, fall back to manual wait."""
    print(f"Logging in as {USERNAME}...")
    page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)

    # Try automated login via the new Reddit login form
    try:
        # Username field — it's a faceplate-text-input with shadow DOM
        username_field = page.locator('#login-username')
        username_field.wait_for(state="visible", timeout=10000)
        # Click it, then type (handles shadow DOM better than fill)
        username_field.click()
        time.sleep(0.5)
        page.keyboard.type(USERNAME, delay=random.randint(30, 80))
        print(f"  Username typed: {USERNAME}")
        time.sleep(1)

        # Look for Continue/Next button
        continue_btn = page.locator('button:has-text("Continue"), button:has-text("Continuar"), faceplate-button:has-text("Continue")')
        if continue_btn.count() > 0 and continue_btn.first.is_visible():
            continue_btn.first.click()
            time.sleep(3)

        # Password field
        password_field = page.locator('#login-password')
        password_field.wait_for(state="visible", timeout=10000)
        password_field.click()
        time.sleep(0.5)
        page.keyboard.type(os.getenv("REDDIT_PASSWORD", ""), delay=random.randint(30, 80))
        print("  Password typed")
        time.sleep(1)

        # Submit login
        login_btn = page.locator('button:has-text("Log In"), button:has-text("Iniciar sesión"), faceplate-button:has-text("Log In")')
        if login_btn.count() > 0:
            login_btn.first.click()
            print("  Login submitted, waiting...")
            time.sleep(8)

            # Check for CAPTCHA or 2FA
            _dismiss_popups(page)
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(4)
            _dismiss_popups(page)

            if is_logged_in(page):
                print("  Automated login successful!")
                return True
            else:
                print("  Automated login may have hit CAPTCHA. Waiting for manual intervention...")

    except Exception as e:
        print(f"  Automated login failed: {e}")
        print("  Falling back to manual login...")

    # Manual fallback
    print(f"  Please log in manually in the browser window. Waiting {timeout}s...")
    for i in range(timeout // 5):
        time.sleep(5)
        cookies = ctx.cookies()
        has_session = any(c["name"] == "reddit_session" for c in cookies)
        has_token = any(c["name"] == "token_v2" for c in cookies)
        if has_session or has_token:
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(4)
            _dismiss_popups(page)
            if is_logged_in(page):
                return True
        if (i + 1) % 6 == 0:
            print(f"  Still waiting... ({(i+1)*5}s)")

    return False


def is_logged_in(page):
    """Check if currently logged in on new reddit. Reliable check using header buttons."""
    # Use Playwright locators — they handle shadow DOM
    # If "Iniciar sesión" / "Log In" button is visible in header, NOT logged in
    login_btn = page.locator('a:has-text("Iniciar sesión"), a:has-text("Log In"), a:has-text("Sign In")')
    register_btn = page.locator('a:has-text("Registrate"), a:has-text("Sign Up")')

    if login_btn.count() > 0 or register_btn.count() > 0:
        try:
            if login_btn.first.is_visible():
                return False
        except Exception:
            pass
        try:
            if register_btn.first.is_visible():
                return False
        except Exception:
            pass

    # If we can't find login buttons, assume logged in
    return True


def do_comment(page, post_id, text):
    """Post a top-level comment on a post via old.reddit.com API."""
    print(f"Commenting on post {post_id}...")
    _ensure_old_reddit(page)

    thing_id = post_id if post_id.startswith('t3_') else f"t3_{post_id}"
    result = _reddit_api(page, 'comment', {'thing_id': thing_id, 'text': text})
    print(f"  API result: {json.dumps(result)}")

    if result.get('ok'):
        things = result.get('data', {}).get('things', [])
        cid = things[0]['data']['id'] if things else '?'
        return f"OK: Comment posted on {post_id} (id: {cid})"
    return f"ERROR: {result.get('error', 'unknown')}"


def _get_modhash(page):
    """Get modhash from old.reddit.com page context."""
    return page.evaluate("""() => {
        try { if (window.reddit && reddit.modhash) return reddit.modhash; } catch(e) {}
        const mh = document.querySelector('input[name="uh"]');
        return mh ? mh.value : '';
    }""")


def _ensure_old_reddit(page):
    """Navigate to old.reddit.com if not there already."""
    if 'old.reddit.com' not in page.url:
        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)


def _reddit_api(page, endpoint, params):
    """Call a Reddit API endpoint from the page context (authenticated via cookies)."""
    return page.evaluate("""(args) => {
        const [endpoint, params] = args;
        return new Promise((resolve) => {
            let modhash = '';
            try { modhash = window.reddit?.modhash || ''; } catch(e) {}
            if (!modhash) {
                const mh = document.querySelector('input[name="uh"]');
                if (mh) modhash = mh.value;
            }
            if (!modhash) { resolve({ok: false, error: 'no_modhash'}); return; }

            const body = new URLSearchParams({...params, uh: modhash, api_type: 'json'});
            fetch('https://old.reddit.com/api/' + endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: body.toString(),
                credentials: 'same-origin',
            })
            .then(r => r.json())
            .then(data => {
                if (data.json?.errors?.length > 0) {
                    resolve({ok: false, error: JSON.stringify(data.json.errors)});
                } else {
                    resolve({ok: true, data: data.json?.data || data});
                }
            })
            .catch(e => resolve({ok: false, error: e.message}));
        });
    }""", [endpoint, params])


def do_reply(page, comment_id, post_id, text):
    """Reply to a comment via old.reddit.com API."""
    print(f"Replying to comment {comment_id}...")
    _ensure_old_reddit(page)

    thing_id = comment_id if comment_id.startswith('t1_') else f"t1_{comment_id}"
    result = _reddit_api(page, 'comment', {'thing_id': thing_id, 'text': text})
    print(f"  API result: {json.dumps(result)}")

    if result.get('ok'):
        things = result.get('data', {}).get('things', [])
        cid = things[0]['data']['id'] if things else '?'
        return f"OK: Reply posted (id: {cid})"
    return f"ERROR: {result.get('error', 'unknown')}"


def do_post(page, subreddit, title, body):
    """Submit a text post via old.reddit.com API."""
    print(f"Posting to r/{subreddit}...")
    _ensure_old_reddit(page)

    result = _reddit_api(page, 'submit', {
        'sr': subreddit,
        'kind': 'self',
        'title': title,
        'text': body,
        'sendreplies': 'true',
    })
    print(f"  API result: {json.dumps(result)}")

    if result.get('ok'):
        post_url = result.get('data', {}).get('url', '')
        return f"OK: Post submitted to r/{subreddit} — {post_url}"
    return f"ERROR: {result.get('error', 'unknown')}"


def do_delete(page, thing_id):
    """Delete a comment or post."""
    print(f"Deleting {thing_id}...")
    _ensure_old_reddit(page)
    result = _reddit_api(page, 'del', {'id': thing_id})
    print(f"  API result: {json.dumps(result)}")
    if result.get('ok'):
        return f"OK: Deleted {thing_id}"
    return f"ERROR: {result.get('error', 'unknown')}"


def run_command(page, cmd_str):
    """Parse and execute a command string."""
    parts = cmd_str.strip().split(maxsplit=1)
    if not parts:
        return "ERROR: Empty command"

    action = parts[0].lower()

    if action == "comment" and len(parts) > 1:
        rest = parts[1].split(maxsplit=1)
        if len(rest) == 2:
            return do_comment(page, rest[0], rest[1])
        return "ERROR: Usage: comment <post_id> <text>"

    elif action == "reply" and len(parts) > 1:
        rest = parts[1].split(maxsplit=2)
        if len(rest) == 3:
            return do_reply(page, rest[0], rest[1], rest[2])
        return "ERROR: Usage: reply <comment_id> <post_id> <text>"

    elif action == "post" and len(parts) > 1:
        rest = parts[1].split(maxsplit=2)
        if len(rest) == 3:
            return do_post(page, rest[0], rest[1], rest[2])
        return "ERROR: Usage: post <subreddit> <title> <body>"

    elif action == "delete" and len(parts) > 1:
        thing_id = parts[1].strip()
        return do_delete(page, thing_id)

    elif action == "screenshot":
        page.screenshot(path="reddit_current.png")
        return "OK: Screenshot saved to reddit_current.png"

    elif action == "status":
        logged = is_logged_in(page)
        return f"OK: logged_in={logged} url={page.url}"

    else:
        return f"ERROR: Unknown command: {action}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", help="Single command to execute then exit")
    parser.add_argument("--wait", type=int, default=180, help="Login wait timeout")
    args = parser.parse_args()

    print("Starting Reddit session...")
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=False,
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
    )
    page = ctx.new_page()

    # Check if already logged in
    page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    _dismiss_popups(page)
    time.sleep(1)

    if not is_logged_in(page):
        print("Not logged in. Starting login flow...")
        success = do_login(page, ctx, args.wait)
        if not success:
            print("Login timed out. Exiting.")
            ctx.close()
            pw.stop()
            return
        print("Login confirmed!")
    else:
        print("Already logged in!")

    # Execute single command if provided
    if args.cmd:
        result = run_command(page, args.cmd)
        print(result)
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        # File-based command loop: watch for .reddit-cmd.txt
        print(f"\nSession active. Write commands to {CMD_FILE}")
        print("Commands: comment <id> <text> | reply <cid> <pid> <text> | post <sub> <title> <body> | screenshot | status")
        print("Write 'quit' to exit.\n")

        while True:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE, "r", encoding="utf-8") as f:
                    cmd = f.read().strip()
                os.remove(CMD_FILE)

                if cmd.lower() == "quit":
                    print("Quitting...")
                    break

                result = run_command(page, cmd)
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
