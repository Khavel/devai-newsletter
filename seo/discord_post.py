"""Post a message (optionally with an image) to a Discord channel via an incoming WEBHOOK.

No bot token, no gateway — incoming webhooks cover the whole auto-post pipeline (messages,
embeds, image attachments). Mirrors telegram_post.py: thin live I/O wrapper; the F1 operator
lint (single source of truth) is imported from the hub lib and runs before any send.

Usage:
  python discord_post.py --webhook-env DISCORD_WEBHOOK_NBA_FREE_PICKS --product nbaproplab \
      --content "Good-tier model report ..." [--image card.png] [--username "NbaPropLab"] [--dry-run]
  # image as an embed from a public URL (e.g. the pick-card endpoint):
  python discord_post.py --webhook-env DISCORD_WEBHOOK_NBA_FREE_PICKS --product nbaproplab \
      --content "..." --image-url https://nbaproplab.com/api/v1/screenshots/pick/123.png

Credentials: the webhook URL is read from ../.env (devai-newsletter root, NEVER committed) by the
key name passed to --webhook-env. Webhook URLs live ONLY in the sibling repo .env, never the hub.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # type: ignore
except Exception:
    guardrails = None

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR.parent / ".env"
LOG_FILE = SCRIPT_DIR / "discord_post_log.jsonl"
RECORD_RUN = _HUB_LIB / "record_run.py"
# Discord/Cloudflare BLOCK the default urllib User-Agent (403 / Cloudflare error 1010).
# A non-default UA is mandatory; Discord asks for the "DiscordBot (url, version)" form.
USER_AGENT = "DiscordBot (https://nbaproplab.com, 1.0)"

# own_domains per product drive the F1 lint (own CTAs allowed; operator links blocked).
OWN_DOMAINS = {
    "nbaproplab": ["nbaproplab.com", "whop.com/nbaproplab", "t.me/nbaproplab_vip", "discord.gg/nbaproplab"],
    "futpicks": ["futpicks.com", "t.me/futpicks_vip", "discord.gg/futpicks"],
}


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_webhook(key: str):
    env = load_env()
    url = env.get(key) or os.getenv(key)
    if not url:
        print(f"ERROR: webhook key {key} not set in {ENV_FILE}")
        sys.exit(1)
    return url


def _post(req, max_tries=5):
    """POST with client-side backoff on 429/5xx honoring Retry-After (Discord gives no retry)."""
    delay = 1.0
    for attempt in range(max_tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return {"ok": True, "status": r.status, "body": r.read().decode("utf-8", "replace")}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
            if e.code == 429 or 500 <= e.code < 600:
                retry_after = e.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else delay
                if attempt < max_tries - 1:
                    time.sleep(min(wait, 30)); delay *= 2; continue
            return {"ok": False, "error": f"HTTP {e.code}: {body[:300]}"}
        except Exception as e:
            if attempt < max_tries - 1:
                time.sleep(delay); delay *= 2; continue
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "exhausted retries"}


def send_text(webhook: str, content: str, username: str, image_url: str = None):
    """Plain JSON post; image_url (public) becomes an embed image."""
    payload = {"content": content, "allowed_mentions": {"parse": []}}
    if username:
        payload["username"] = username
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook + "?wait=true", data=data,
                                headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    return _post(req)


def send_image(webhook: str, content: str, username: str, image_path: str):
    """multipart/form-data: payload_json + files[0], embed references attachment://<name>."""
    p = Path(image_path)
    try:
        file_bytes = p.read_bytes()
    except Exception as e:
        return {"ok": False, "error": f"cannot read image: {e}"}
    payload = {"content": content, "allowed_mentions": {"parse": []},
               "embeds": [{"image": {"url": f"attachment://{p.name}"}}]}
    if username:
        payload["username"] = username
    boundary = "----discordpost%d" % int(datetime.now().timestamp())
    parts = []
    parts.append(("--" + boundary).encode())
    parts.append(b'Content-Disposition: form-data; name="payload_json"')
    parts.append(b"Content-Type: application/json")
    parts.append(b"")
    parts.append(json.dumps(payload).encode("utf-8"))
    parts.append(("--" + boundary).encode())
    parts.append(('Content-Disposition: form-data; name="files[0]"; filename="%s"' % p.name).encode())
    parts.append(b"Content-Type: application/octet-stream")
    parts.append(b"")
    parts.append(file_bytes)
    parts.append(("--" + boundary + "--").encode())
    parts.append(b"")
    body = b"\r\n".join(parts)
    req = urllib.request.Request(webhook + "?wait=true", data=body,
                                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary,
                                         "User-Agent": USER_AGENT})
    return _post(req)


def log_post(product: str, content: str, link: str, media: bool):
    now = datetime.now(timezone.utc)
    entry = {"timestamp": now.strftime("%Y-%m-%dT%H:%M:%S+00:00"), "date": now.strftime("%Y-%m-%d"),
             "time": now.strftime("%H:%M:%S"), "product": product, "platform": "discord",
             "link": link, "text_preview": content[:100] + ("..." if len(content) > 100 else ""),
             "method": "webhook", "media": media}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Logged to {LOG_FILE.name}")


def record_run(product: str, link: str):
    if not RECORD_RUN.exists():
        return
    args = [sys.executable, str(RECORD_RUN), "--routine", f"{product}-discord", "--product", product,
            "--category", "discord", "--summary", "Discord webhook post"]
    if link:
        args += ["--link", "post|" + link]
    try:
        subprocess.run(args, check=False)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="Post to Discord via an incoming webhook (F1-linted)")
    ap.add_argument("--webhook-env", required=True, help="env key name holding the webhook URL")
    ap.add_argument("--product", required=True, choices=list(OWN_DOMAINS.keys()))
    ap.add_argument("--content", help="message text (or use --file)")
    ap.add_argument("--file", help="read message text from a file")
    ap.add_argument("--image", help="local image to attach (multipart)")
    ap.add_argument("--image-url", dest="image_url", help="public image URL (embed)")
    ap.add_argument("--username", help="override webhook display name")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    content = a.content if a.content else (Path(a.file).read_text(encoding="utf-8").strip() if a.file else "")
    if not content:
        print("ERROR: --content or --file required"); sys.exit(2)

    # F1 lint (single source of truth) — own CTAs OK, operator links/guarantee BLOCKED.
    if guardrails is not None:
        violations = guardrails.lint_text(content, own_domains=OWN_DOMAINS[a.product])
        if violations:
            print("BLOCKED by guardrails:")
            for v in violations:
                print(f"  - {v}")
            sys.exit(3)
    else:
        print("WARN: guardrails not importable — manual F1 review required before relying on this.")

    if a.dry_run:
        print(f"[DRY RUN] product={a.product} webhook-env={a.webhook_env}")
        if a.image: print(f"[DRY RUN] image={a.image}")
        if a.image_url: print(f"[DRY RUN] image_url={a.image_url}")
        print("[DRY RUN] content:\n" + content)
        return

    webhook = get_webhook(a.webhook_env)
    if a.image:
        res = send_image(webhook, content, a.username, a.image)
    else:
        res = send_text(webhook, content, a.username, a.image_url)
    if res["ok"]:
        link = ""
        try:
            link = (json.loads(res["body"]).get("id") or "") if res.get("body") else ""
        except Exception:
            pass
        print(f"  Sent (status {res.get('status')}, msg id {link or '?'})")
        log_post(a.product, content, link, media=bool(a.image))
        record_run(a.product, link)
    else:
        print(f"  Failed: {res['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
