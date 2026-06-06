"""
Reddit agent for DevAI Semanal promotion via Khavel_dev account.

Reading: public .json endpoints (no auth, no API key)
Writing: Playwright browser automation (persistent session)

Usage:
  python reddit_agent.py login                         # First-time login (manual CAPTCHA if needed)
  python reddit_agent.py karma                         # Check account age & karma
  python reddit_agent.py browse <subreddit>            # Hot posts
  python reddit_agent.py browse <subreddit> --new      # New posts
  python reddit_agent.py read <post_id>                # Read post + comments
  python reddit_agent.py search <subreddit> "query"    # Search subreddit
  python reddit_agent.py comment <post_id> "text"      # Post a comment
  python reddit_agent.py reply <comment_id> <post_url> "text"  # Reply to comment
  python reddit_agent.py post <subreddit> "title" "body"       # Submit new post
"""

import argparse
import json
import os
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

# Reuse the hub's reddit account registry (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import reddit_accounts  # type: ignore
except Exception:
    reddit_accounts = None

# Defaults (legacy Khavel_dev). resolve_account(name) overrides these at runtime in main().
_DEFAULT_ACCT = reddit_accounts.resolve_account(None) if reddit_accounts else None
PROFILE_DIR = _DEFAULT_ACCT["profile_dir"] if _DEFAULT_ACCT else str(Path(__file__).parent / ".reddit-profile")
COOKIES_FILE = str(Path(__file__).parent / ".reddit-cookies.json")
USERNAME = _DEFAULT_ACCT["username"] if _DEFAULT_ACCT else "Khavel_dev"
UA = (_DEFAULT_ACCT["user_agent"] if _DEFAULT_ACCT
      else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
JSON_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"}


# ══════════════════════════════════════════════════════════════════════════════
#  READ LAYER — public .json endpoints (no auth)
# ══════════════════════════════════════════════════════════════════════════════

def _get_json(path: str, params: dict = None) -> dict:
    url = f"https://www.reddit.com{path}.json"
    r = httpx.get(url, headers=JSON_HEADERS, params=params or {}, timeout=15, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def fmt_age(utc_ts: float) -> str:
    age = datetime.now(tz=timezone.utc) - datetime.fromtimestamp(utc_ts, tz=timezone.utc)
    if age.days > 0:
        return f"{age.days}d"
    h = age.seconds // 3600
    return f"{h}h" if h > 0 else f"{age.seconds // 60}m"


def cmd_browse(args):
    sort = "new" if args.new else "hot"
    data = _get_json(f"/r/{args.subreddit}/{sort}", {"limit": str(args.limit)})
    posts = data["data"]["children"]

    print(f"\n{'NEW' if args.new else 'HOT'} in r/{args.subreddit}  ({len(posts)} posts)\n")
    print(f"{'#':<3} {'Pts':<6} {'Cmt':<5} {'Age':<5} Title")
    print("-" * 85)

    for i, p in enumerate(posts, 1):
        d = p["data"]
        title = textwrap.shorten(d["title"], width=58, placeholder="...")
        print(f"{i:<3} {d['score']:<6} {d['num_comments']:<5} {fmt_age(d['created_utc']):<5} {title}")
        print(f"    id:{d['id']}  u/{d['author']}  {'[link]' if not d['is_self'] else ''}")
    print()


def cmd_read(args):
    post_id = args.post_id.split("/")[-1] if "/" in args.post_id else args.post_id
    data = _get_json(f"/comments/{post_id}", {"limit": str(args.comments), "sort": "best"})

    post = data[0]["data"]["children"][0]["data"]
    comments = data[1]["data"]["children"]

    print(f"\n{'=' * 80}")
    print(f"r/{post['subreddit']}  |  {post['score']} pts  |  {post['num_comments']} comments  |  {fmt_age(post['created_utc'])}")
    print(f"u/{post['author']}  |  id:{post['id']}")
    print(f"\n{post['title']}")
    print(f"{'=' * 80}")

    if post.get("selftext"):
        body = post["selftext"][:2000]
        print(f"\n{body}")
        if len(post["selftext"]) > 2000:
            print(f"\n... [{len(post['selftext'])} chars total]")

    print(f"\n{'─' * 80}")
    print(f"COMMENTS:\n")

    for i, c in enumerate(comments, 1):
        if c["kind"] != "t1":
            continue
        cd = c["data"]
        body = textwrap.shorten(cd.get("body", ""), width=300, placeholder="...")
        author = cd.get("author", "[deleted]")
        print(f"  [{i}] u/{author}  |  {cd.get('score', 0)} pts  |  {fmt_age(cd['created_utc'])}  |  id:{cd['id']}")
        print(f"      {body}")
        print()


def cmd_search(args):
    data = _get_json(f"/r/{args.subreddit}/search", {
        "q": args.query, "restrict_sr": "1", "sort": "relevance",
        "t": "month", "limit": str(args.limit),
    })
    posts = data["data"]["children"]

    print(f"\nSearch '{args.query}' in r/{args.subreddit}  ({len(posts)} results)\n")
    print(f"{'#':<3} {'Pts':<6} {'Cmt':<5} {'Age':<5} Title")
    print("-" * 85)

    for i, p in enumerate(posts, 1):
        d = p["data"]
        title = textwrap.shorten(d["title"], width=58, placeholder="...")
        print(f"{i:<3} {d['score']:<6} {d['num_comments']:<5} {fmt_age(d['created_utc']):<5} {title}")
        print(f"    id:{d['id']}  u/{d['author']}")
    print()


def cmd_karma(args):
    data = _get_json(f"/user/{USERNAME}/about")
    u = data["data"]
    created = datetime.fromtimestamp(u["created_utc"], tz=timezone.utc)
    age_days = (datetime.now(tz=timezone.utc) - created).days

    print(f"\nAccount: u/{u['name']}")
    print(f"Created: {created.strftime('%Y-%m-%d')}")
    print(f"Comment karma: {u.get('comment_karma', 0)}")
    print(f"Post karma:    {u.get('link_karma', 0)}")
    print(f"Total karma:   {u.get('comment_karma', 0) + u.get('link_karma', 0)}")
    print(f"Account age:   {age_days} days")

    if age_days < 14:
        print(f"\n⚠️  {14 - age_days} days until safe to post promotional content")
    if u.get("comment_karma", 0) < 100:
        print(f"⚠️  Comment karma {u.get('comment_karma', 0)}/100 target")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE LAYER — Playwright browser automation (persistent session)
# ══════════════════════════════════════════════════════════════════════════════

def _get_browser(headless=False):
    """Launch persistent Chromium context — keeps cookies, localStorage, etc. across runs."""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    # launch_persistent_context IS the context — it returns a BrowserContext directly
    context = pw.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        viewport={"width": 1280, "height": 900},
        user_agent=UA,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )
    # browser object is context itself for persistent contexts
    return pw, context, context


def _human_delay(min_s=1.5, max_s=3.5):
    import random
    time.sleep(random.uniform(min_s, max_s))


def _type_human(page, selector, text):
    """Type text character by character with random delays to mimic human typing."""
    import random
    el = page.locator(selector).first
    el.click()
    time.sleep(0.3)
    for char in text:
        el.type(char, delay=random.randint(30, 120))


def cmd_login(args):
    print(f"Opening browser for login as u/{USERNAME}...")
    print(f"Profile will be saved to: {PROFILE_DIR}\n")

    wait_seconds = getattr(args, "wait", 120)

    pw, browser, context = _get_browser(headless=False)
    page = context.new_page()

    page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded", timeout=60000)
    print("Reddit login page loaded.")
    print(f"You have {wait_seconds} seconds to log in manually (handle any CAPTCHA).")
    print("Waiting...\n")

    # Poll until logged in or timeout
    logged_in = False
    for i in range(wait_seconds // 5):
        time.sleep(5)
        cookies = context.cookies()
        session_cookies = [c for c in cookies if "reddit" in c.get("domain", "") and c["name"] in ("reddit_session", "token_v2", "loid")]
        if len(session_cookies) >= 2:
            logged_in = True
            print(f"   Detected login cookies after {(i+1)*5}s")
            break
        if (i + 1) % 6 == 0:
            print(f"   Still waiting... ({(i+1)*5}s elapsed)")

    if not logged_in:
        # Final check — navigate to reddit and see if username appears
        page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)

    cookies = context.cookies()
    reddit_cookies = [c for c in cookies if "reddit" in c.get("domain", "")]

    if len(reddit_cookies) > 5:
        print(f"\n[OK] Session persisted with {len(reddit_cookies)} Reddit cookies")
        print(f"   Profile dir: {PROFILE_DIR}")
        print(f"   Persistent context keeps cookies on disk automatically.\n")
    else:
        print(f"\n[WARN] Only {len(reddit_cookies)} cookies found. Login may have failed.")
        print(f"   Run 'login' again if needed.\n")

    context.close()
    pw.stop()


def _dismiss_popups(page):
    """Dismiss cookie banners, consent dialogs, and other popups."""
    page.evaluate("""() => {
        // Cookie consent buttons (Reddit, EU compliance)
        const selectors = [
            'button:has-text("Accept")', 'button:has-text("Aceptar")',
            'button:has-text("Accept all")', 'button:has-text("Aceptar todo")',
            'button:has-text("Rechazar cookies no esenciales")',
            'button:has-text("Reject non-essential")',
            '[data-testid="cookie-policy-banner-accept"]',
            '.cookie-infobar button', '.consent-btn',
        ];
        for (const sel of selectors) {
            try {
                const el = document.querySelector(sel);
                if (el && el.offsetParent !== null) { el.click(); return; }
            } catch(e) {}
        }
        // Try shadow DOM (new reddit uses web components)
        try {
            const banners = document.querySelectorAll('shreddit-cookie-policy, reddit-cookie-banner');
            for (const b of banners) {
                const shadow = b.shadowRoot;
                if (shadow) {
                    const btn = shadow.querySelector('button');
                    if (btn) btn.click();
                }
            }
        } catch(e) {}
    }""")
    time.sleep(1)


def _ensure_old_reddit(page, path):
    """Navigate using old.reddit.com — simpler DOM, easier to automate."""
    url = f"https://old.reddit.com{path}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    _dismiss_popups(page)
    time.sleep(1)
    return page


def cmd_comment(args):
    print(f"Posting comment on post {args.post_id}...")

    pw, browser, context = _get_browser(headless=False)
    page = context.new_page()

    success = False

    # ── Attempt 1: old.reddit.com ──────────────────────────────────────
    try:
        _ensure_old_reddit(page, f"/comments/{args.post_id}")

        # Check if logged in on old reddit
        logged_in = page.evaluate("""() => {
            const user = document.querySelector('.user a, #header .user');
            return user ? user.textContent : null;
        }""")
        print(f"   Old reddit user: {logged_in or 'not logged in'}")

        if not logged_in:
            print("   Not logged in on old.reddit — trying new reddit...")
            raise Exception("not logged in on old reddit")

        comment_box = page.locator('.commentarea textarea[name="text"], .usertext-edit textarea')
        comment_box.first.wait_for(state="visible", timeout=8000)
        _human_delay(1, 2)
        comment_box.first.click()
        _human_delay(0.5, 1)
        comment_box.first.fill(args.text)
        _human_delay(1, 2)

        save_btn = page.locator('.commentarea button[type="submit"], .commentarea .save-form button')
        save_btn.first.click()
        print("   Submitted on old reddit, waiting...")
        _human_delay(3, 5)

        error = page.locator('.error, .status-msg.error')
        if error.count() > 0 and error.first.is_visible():
            err_text = error.first.text_content()
            print(f"   Error: {err_text}")
        else:
            print(f"   [OK] Comment posted on post {args.post_id} (old reddit)")
            success = True

    except Exception as e:
        print(f"   Old reddit attempt: {e}")

    # ── Attempt 2: new reddit (www.reddit.com) ─────────────────────────
    if not success:
        try:
            print("   Trying new Reddit...")
            page.goto(f"https://www.reddit.com/comments/{args.post_id}/",
                       wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            _dismiss_popups(page)
            time.sleep(2)

            # New reddit: click on comment area to activate it
            # The comment composer might be a shreddit-composer or a div with contenteditable
            # First try clicking a placeholder like "Add a comment"
            placeholder = page.locator(
                'div[placeholder*="comment" i], '
                'div[data-placeholder*="comment" i], '
                'p[data-placeholder*="comment" i], '
                '[role="textbox"][placeholder*="comment" i], '
                'shreddit-composer, '
                'faceplate-form'
            )

            if placeholder.count() > 0:
                placeholder.first.click()
                _human_delay(1, 2)

            # Now find the active text input
            text_input = page.locator(
                '[contenteditable="true"][role="textbox"], '
                'div[data-lexical-editor="true"], '
                '[contenteditable="true"]'
            )
            text_input.first.wait_for(state="visible", timeout=10000)
            text_input.first.click()
            _human_delay(0.5, 1)

            # Type the comment (keyboard.type handles contenteditable better than fill)
            page.keyboard.type(args.text, delay=30)
            _human_delay(1, 2)

            # Find and click the Comment/submit button
            submit_btn = page.locator(
                'button:has-text("Comment"):not([disabled]), '
                'faceplate-button:has-text("Comment"), '
                'button[type="submit"]:has-text("Comment"), '
                'button[slot="submit-button"]'
            )
            submit_btn.first.wait_for(state="visible", timeout=5000)
            submit_btn.first.click()
            print("   Submitted on new reddit, waiting...")
            _human_delay(4, 6)

            print(f"   [OK] Comment posted on post {args.post_id} (new reddit)")
            success = True

        except Exception as e2:
            print(f"   New reddit attempt: {e2}")
            page.screenshot(path="reddit_comment_debug.png")
            print("   Screenshot saved to reddit_comment_debug.png")

    # ── Attempt 3: direct URL with ?context ────────────────────────────
    if not success:
        try:
            print("   Final attempt: navigating to full post URL...")
            # Get the actual permalink from .json
            data = _get_json(f"/comments/{args.post_id}")
            permalink = data[0]["data"]["children"][0]["data"]["permalink"]
            page.goto(f"https://www.reddit.com{permalink}", wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
            _dismiss_popups(page)
            time.sleep(2)

            # Dump the page HTML to debug
            page.screenshot(path="reddit_comment_debug.png")
            html = page.content()
            with open("reddit_comment_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   Saved debug screenshot and HTML")
            print("   Comment NOT posted. Check reddit_comment_debug.png")

        except Exception as e3:
            print(f"   Final attempt failed: {e3}")

    context.close()
    pw.stop()


def cmd_reply(args):
    print(f"Replying to comment {args.comment_id}...")

    pw, browser, context = _get_browser(headless=False)
    page = context.new_page()

    # Navigate to the post, then find the specific comment
    _ensure_old_reddit(page, args.post_url)

    try:
        # Find the reply link for the specific comment
        comment_el = page.locator(f'#thing_t1_{args.comment_id}, div[data-fullname="t1_{args.comment_id}"]')
        if comment_el.count() == 0:
            # Try scrolling to find it
            page.evaluate(f"""() => {{
                const el = document.getElementById('thing_t1_{args.comment_id}');
                if (el) el.scrollIntoView();
            }}""")
            time.sleep(1)

        # Click "reply" link on old reddit
        reply_link = page.locator(f'#thing_t1_{args.comment_id} .flat-list a:has-text("reply"), #thing_t1_{args.comment_id} a[onclick*="reply"]').first
        reply_link.click()
        _human_delay(1, 2)

        # Fill the reply textarea
        reply_box = page.locator(f'#thing_t1_{args.comment_id} textarea[name="text"]').first
        reply_box.wait_for(state="visible", timeout=5000)
        reply_box.fill(args.text)
        _human_delay(1, 2)

        # Submit
        save_btn = page.locator(f'#thing_t1_{args.comment_id} button[type="submit"]:has-text("save")').first
        save_btn.click()
        _human_delay(3, 5)

        print(f"   ✅ Reply posted to comment {args.comment_id}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        page.screenshot(path="reddit_reply_debug.png")
        print("   Screenshot saved to reddit_reply_debug.png")

    context.close()
    pw.stop()


def cmd_post(args):
    print(f"Submitting post to r/{args.subreddit}...")

    pw, browser, context = _get_browser(headless=False)
    page = context.new_page()

    _ensure_old_reddit(page, f"/r/{args.subreddit}/submit")

    try:
        # Select "text" tab on old reddit
        text_tab = page.locator('a.text-button, li.text-button a, a:has-text("text")').first
        if text_tab.is_visible():
            text_tab.click()
            _human_delay(1, 2)

        # Title
        title_input = page.locator('textarea[name="title"], input[name="title"]').first
        title_input.wait_for(state="visible", timeout=10000)
        title_input.fill(args.title)
        _human_delay(1, 2)

        # Body
        body_input = page.locator('textarea[name="text"], .usertext-edit textarea').first
        body_input.fill(args.body)
        _human_delay(1, 2)

        # Submit
        submit_btn = page.locator('button[type="submit"]:has-text("submit"), button:has-text("Submit"), #submit_btn').first
        submit_btn.click()
        print("   Submitted, waiting...")
        _human_delay(5, 8)

        # Check result
        current_url = page.url
        if "/comments/" in current_url:
            print(f"   ✅ Post submitted: {current_url}")
        else:
            error = page.locator('.error, .status-msg')
            if error.count() > 0:
                print(f"   ❌ Error: {error.first.text_content()}")
            else:
                print(f"   ⚠️  Unclear result. Current URL: {current_url}")
                page.screenshot(path="reddit_post_debug.png")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        page.screenshot(path="reddit_post_debug.png")
        print("   Screenshot saved to reddit_post_debug.png")

    context.close()
    pw.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    global PROFILE_DIR, USERNAME, UA
    parser = argparse.ArgumentParser(description="Reddit agent — .json reads + Playwright writes")
    parser.add_argument("--account", default=None, help="Reddit persona (default Khavel_dev)")
    # Shared parent so --account is also accepted AFTER the subcommand
    # (e.g. `reddit_agent.py browse dotnet --account Khavel_dev`).
    acct_parent = argparse.ArgumentParser(add_help=False)
    # SUPPRESS so this only sets `account` when given after the subcommand,
    # never clobbering a value parsed before the subcommand.
    acct_parent.add_argument("--account", default=argparse.SUPPRESS,
                             help="Reddit persona (default Khavel_dev)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", parents=[acct_parent], help="Log in via browser (one-time setup)")
    p_login.add_argument("--wait", type=int, default=120, help="Seconds to wait for manual login")
    p_login.set_defaults(func=cmd_login)

    p_karma = sub.add_parser("karma", parents=[acct_parent], help="Check account karma & age")
    p_karma.set_defaults(func=cmd_karma)

    p_browse = sub.add_parser("browse", parents=[acct_parent], help="Browse subreddit")
    p_browse.add_argument("subreddit")
    p_browse.add_argument("--new", action="store_true")
    p_browse.add_argument("--limit", type=int, default=15)
    p_browse.set_defaults(func=cmd_browse)

    p_read = sub.add_parser("read", parents=[acct_parent], help="Read post + comments")
    p_read.add_argument("post_id")
    p_read.add_argument("--comments", type=int, default=10)
    p_read.set_defaults(func=cmd_read)

    p_search = sub.add_parser("search", parents=[acct_parent], help="Search subreddit")
    p_search.add_argument("subreddit")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=15)
    p_search.set_defaults(func=cmd_search)

    p_comment = sub.add_parser("comment", parents=[acct_parent], help="Comment on a post")
    p_comment.add_argument("post_id")
    p_comment.add_argument("text")
    p_comment.set_defaults(func=cmd_comment)

    p_reply = sub.add_parser("reply", parents=[acct_parent], help="Reply to a comment")
    p_reply.add_argument("comment_id")
    p_reply.add_argument("post_url", help="Post URL path like /comments/xxxxx")
    p_reply.add_argument("text")
    p_reply.set_defaults(func=cmd_reply)

    p_post = sub.add_parser("post", parents=[acct_parent], help="Submit a new post")
    p_post.add_argument("subreddit")
    p_post.add_argument("title")
    p_post.add_argument("body")
    p_post.set_defaults(func=cmd_post)

    parsed = parser.parse_args()

    if reddit_accounts:
        acct = reddit_accounts.resolve_account(parsed.account)
        PROFILE_DIR = acct["profile_dir"]
        USERNAME = acct["username"]
        UA = acct["user_agent"]

    parsed.func(parsed)


if __name__ == "__main__":
    main()
