"""
Create a Reddit API 'script' app via Playwright browser automation.
Reddit uses faceplate web components with shadow DOM, so we use JS to interact.
"""

import json
import re
import sys
import time

from playwright.sync_api import sync_playwright

USERNAME = "Khavel_dev"
PASSWORD = os.getenv("REDDIT_PASSWORD", "")
APP_NAME = "devai-agent"
REDIRECT_URI = "http://localhost:8080"
OUTPUT_FILE = "reddit_app_credentials.json"


def js_fill(page, selector, value):
    """Fill a faceplate-text-input by finding the real <input> inside shadow DOM."""
    page.evaluate(f"""() => {{
        const el = document.querySelector('{selector}');
        if (!el) throw new Error('Element not found: {selector}');
        // faceplate-text-input wraps a real input in shadow DOM
        const input = el.shadowRoot ? el.shadowRoot.querySelector('input') : el;
        if (!input) throw new Error('No input inside shadow: {selector}');
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(input, '{value}');
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # ── Step 1: Login via old.reddit.com ──────────────────────────────
        # old.reddit.com has standard HTML forms, much easier to automate
        print("[1/4] Logging in via old.reddit.com...")
        page.goto("https://old.reddit.com/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # old.reddit.com login form
        try:
            page.wait_for_selector('form#login-form, form[action*="login"]', timeout=15000)
            # The login form on old reddit has name fields "user" and "passwd"
            page.evaluate(f"""() => {{
                const form = document.querySelector('form#login-form') || document.querySelector('form[action*="login"]');
                if (!form) throw new Error('No login form found');
                const userInput = form.querySelector('input[name="user"]');
                const passInput = form.querySelector('input[name="passwd"]');
                if (!userInput || !passInput) throw new Error('Form inputs not found');
                userInput.value = '{USERNAME}';
                passInput.value = '{PASSWORD}';
            }}""")
            time.sleep(1)

            # Click the login button
            page.evaluate("""() => {
                const form = document.querySelector('form#login-form') || document.querySelector('form[action*="login"]');
                const btn = form.querySelector('button[type="submit"]');
                if (btn) btn.click();
                else form.submit();
            }""")
            print("       Login form submitted")
            time.sleep(5)

        except Exception as e1:
            print(f"       old.reddit.com login failed: {e1}")
            print("       Trying new Reddit login with shadow DOM workaround...")

            page.goto("https://www.reddit.com/login/", wait_until="networkidle", timeout=60000)
            time.sleep(5)

            # New Reddit uses faceplate-text-input web components
            try:
                js_fill(page, '#login-username', USERNAME)
                print(f"       Username filled: {USERNAME}")
                time.sleep(1)

                # Click continue
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const btn of btns) {
                        if (btn.textContent.includes('Continue') || btn.textContent.includes('Continuar') || btn.textContent.includes('Next')) {
                            btn.click();
                            return;
                        }
                    }
                    // Try faceplate-button
                    const fpBtn = document.querySelector('faceplate-button[type="submit"]');
                    if (fpBtn) fpBtn.click();
                }""")
                time.sleep(3)

                js_fill(page, '#login-password', PASSWORD)
                print("       Password filled")
                time.sleep(1)

                # Click login
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button, faceplate-button');
                    for (const btn of btns) {
                        const text = btn.textContent || '';
                        if (text.includes('Log In') || text.includes('Iniciar') || text.includes('Sign in')) {
                            btn.click();
                            return;
                        }
                    }
                }""")
                print("       Login submitted")
                time.sleep(5)

            except Exception as e2:
                print(f"       New Reddit login also failed: {e2}")
                page.screenshot(path="reddit_login_debug.png")
                print("       Screenshot saved. Browser staying open for manual login.")
                print("       Please log in manually, then press Enter...")
                input()

        print(f"       Current URL: {page.url}")

        # ── Step 2: Navigate to old.reddit.com/prefs/apps ────────────────
        print("[2/4] Navigating to app preferences (old reddit)...")
        page.goto("https://old.reddit.com/prefs/apps/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        page_text = page.text_content("body") or ""

        if "create another app" in page_text.lower() or "developed applications" in page_text.lower():
            print("       ✅ On app preferences page")
        elif "log in" in page_text.lower() or "login" in page_text.lower():
            print("       ⚠️  Not logged in. Trying login redirect...")
            # Maybe we need to log in on old.reddit specifically
            page.screenshot(path="reddit_prefs_debug.png")
            print("       Screenshot saved to reddit_prefs_debug.png")
            print("       Browser open — log in manually if needed, then press Enter...")
            input()
            page.goto("https://old.reddit.com/prefs/apps/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        # ── Step 3: Check if app already exists ───────────────────────────
        if APP_NAME.lower() in (page.text_content("body") or "").lower():
            print(f"       App '{APP_NAME}' already exists! Extracting credentials...")
        else:
            # ── Step 3b: Create the app ───────────────────────────────────
            print("[3/4] Creating API app...")

            # Click "create another app..." button at bottom
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    if (btn.textContent.toLowerCase().includes('create another app') ||
                        btn.textContent.toLowerCase().includes('create an app')) {
                        btn.click();
                        return true;
                    }
                }
                // Try link
                const links = document.querySelectorAll('a');
                for (const a of links) {
                    if (a.textContent.toLowerCase().includes('create another app') ||
                        a.textContent.toLowerCase().includes('create an app')) {
                        a.click();
                        return true;
                    }
                }
                return false;
            }""")
            time.sleep(2)

            # Fill app name
            page.evaluate(f"""() => {{
                const input = document.querySelector('#app_name, input[name="name"]');
                if (input) input.value = '{APP_NAME}';
            }}""")
            print(f"       App name: {APP_NAME}")

            # Select "script" radio button
            page.evaluate("""() => {
                const radios = document.querySelectorAll('input[type="radio"]');
                for (const radio of radios) {
                    if (radio.value === 'script' || radio.id === 'app_type_script') {
                        radio.checked = true;
                        radio.click();
                        return;
                    }
                }
            }""")
            print("       Type: script")
            time.sleep(1)

            # Fill redirect URI
            page.evaluate(f"""() => {{
                const input = document.querySelector('#redirect_uri, input[name="redirect_uri"]');
                if (input) input.value = '{REDIRECT_URI}';
            }}""")
            print(f"       Redirect URI: {REDIRECT_URI}")

            # Submit
            page.evaluate("""() => {
                const btn = document.querySelector('.app-form button[type="submit"], input[value="create app"], button.btn');
                if (btn) {
                    btn.click();
                    return true;
                }
                // Try any submit in the create form
                const forms = document.querySelectorAll('form');
                for (const form of forms) {
                    if (form.querySelector('#app_name, input[name="name"]')) {
                        form.submit();
                        return true;
                    }
                }
                return false;
            }""")
            print("       Form submitted!")
            time.sleep(5)

        # ── Step 4: Extract credentials ───────────────────────────────────
        print("[4/4] Extracting credentials...")

        page.screenshot(path="reddit_app_result.png")

        # On old.reddit.com/prefs/apps, the app listing shows:
        # - App name
        # - "personal use script" label
        # - client_id (displayed as plain text, ~22 chars)
        # - secret (shown in the listing)
        creds = page.evaluate(f"""() => {{
            const body = document.body.innerHTML;
            const result = {{}};

            // Find all developed apps
            const apps = document.querySelectorAll('.developed-app');
            for (const app of apps) {{
                const text = app.textContent || '';
                if (text.toLowerCase().includes('{APP_NAME.lower()}')) {{
                    // Client ID is in an <h3> tag or similar, as a short alphanumeric string
                    const h3 = app.querySelector('h3');
                    if (h3) {{
                        // The client ID is often the last child text node of the header area
                        const spans = app.querySelectorAll('span, li, p, h3');
                        for (const span of spans) {{
                            const t = span.textContent.trim();
                            // Client ID is ~14-30 char alphanumeric
                            if (/^[a-zA-Z0-9_-]{{14,30}}$/.test(t)) {{
                                result.client_id = t;
                            }}
                            // Secret is labeled
                            if (t.includes('secret')) {{
                                const next = span.nextElementSibling || span.parentElement.nextElementSibling;
                                if (next) result.client_secret = next.textContent.trim();
                            }}
                        }}
                    }}
                    // Also grab the full text for debugging
                    result.app_text = text.substring(0, 500);
                    break;
                }}
            }}

            // Alternative: scan all text for patterns
            if (!result.client_id) {{
                const allText = document.body.innerText;
                // Find lines near our app name
                const lines = allText.split('\\n').map(l => l.trim()).filter(l => l);
                const appIdx = lines.findIndex(l => l.toLowerCase().includes('{APP_NAME.lower()}'));
                if (appIdx >= 0) {{
                    result.nearby_lines = lines.slice(Math.max(0, appIdx - 2), appIdx + 10);
                }}
            }}

            return result;
        }}""")

        print(f"       Extracted data: {json.dumps(creds, indent=2)}")

        if creds.get("client_id") and creds.get("client_secret"):
            output = {
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "username": USERNAME,
                "app_name": APP_NAME,
                "redirect_uri": REDIRECT_URI,
            }
            with open(OUTPUT_FILE, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\n✅ Credentials saved to {OUTPUT_FILE}")
            print(f"   Client ID: {creds['client_id']}")
            print(f"   Client Secret: {creds['client_secret'][:4]}{'*' * max(0, len(creds['client_secret']) - 4)}")
        else:
            print("\n⚠️  Could not auto-extract all credentials.")
            print("   Screenshot saved to reddit_app_result.png")
            with open("reddit_app_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("   HTML saved to reddit_app_page.html")
            print("   Browser staying open — you can extract manually.")
            input("   Press Enter when done...")

        browser.close()


if __name__ == "__main__":
    main()
