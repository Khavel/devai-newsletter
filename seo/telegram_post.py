"""Post a free-feed -> paid-tier message to a Telegram channel via the Bot API.

Usage:
  python telegram_post.py --channel nba --free "3 props over threshold tonight" \
      --tier "Unlock Pro" --cta-url "https://whop.com/nbaproplab"
  python telegram_post.py --channel devai --free "Free read of the day."
  python telegram_post.py --channel fut --free "..." --photo card.png --dry-run

The pure free-feed -> paid-tier builder + the operator lint both live in the hub
and are imported via the shim below (single source of truth). This file is the thin
live wrapper: it only adds Bot API I/O (stdlib urllib, no extra dep, mirroring the
hub's lib/notify.py Telegram pattern) and per-channel credential resolution.

Credentials come from ../.env (the devai-newsletter root, NEVER committed):
  TELEGRAM_BOT_TOKEN_<NBA|FUT|DEVAI>  per-channel bot token. Each product runs its OWN
                                      bot, and a bot can only post to a channel where it
                                      is an admin, so the per-channel bot must own that
                                      channel. Falls back to the shared TELEGRAM_BOT_TOKEN.
  TELEGRAM_CHAT_NBA / _FUT / _DEVAI   per-channel chat id (no global fallback)
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Reuse the hub's pure builder + guardrails (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import telegram_message  # type: ignore
except Exception:
    telegram_message = None

# Fix Windows console encoding for non-ascii output.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR.parent / ".env"
LOG_FILE = SCRIPT_DIR / "telegram_post_log.jsonl"
RECORD_RUN = _HUB_LIB / "record_run.py"

# Per-channel registry. chat_env is read from ../.env; own_domains drive the lint
# (a CTA to an own destination is allowed, gambling-operator links are blocked).
CHANNELS = {
    "nba": {
        "chat_env": "TELEGRAM_CHAT_NBA",
        "product": "NbaPropLab",
        "username": "nbaproplab",
        "own_domains": ["nbaproplab.com", "whop.com/nbaproplab", "t.me/nbaproplab_vip"],
    },
    "fut": {
        "chat_env": "TELEGRAM_CHAT_FUT",
        "product": "FutPicks",
        "username": "futpicks",
        "own_domains": ["futpicks.com", "whop.com/futpicks", "t.me/futpicks_vip"],
    },
    "devai": {
        "chat_env": "TELEGRAM_CHAT_DEVAI",
        "product": "DevAI Semanal",
        "username": "devaisemanal",
        "own_domains": ["devaisemanal.com"],
    },
}


def load_env():
    """Return a dict of the ../.env key/value pairs (no external dep)."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_credentials(channel: str):
    """Return (token, chat_id) for a channel or exit if missing.

    Bot is resolved per-channel first (TELEGRAM_BOT_TOKEN_<CHANNEL>) because each
    product runs its own bot; falls back to the shared TELEGRAM_BOT_TOKEN. There is
    deliberately NO global TELEGRAM_CHAT_ID fallback: it points at the unrelated
    PlexAnnouncer channel, so a missing per-channel chat id fails loudly rather than
    mis-posting a product drop to the wrong place.
    """
    env = load_env()
    chan = channel.upper()
    token = (
        env.get(f"TELEGRAM_BOT_TOKEN_{chan}")
        or os.getenv(f"TELEGRAM_BOT_TOKEN_{chan}")
        or env.get("TELEGRAM_BOT_TOKEN")
        or os.getenv("TELEGRAM_BOT_TOKEN")
    )
    chat_env = CHANNELS[channel]["chat_env"]
    chat = env.get(chat_env) or os.getenv(chat_env)
    if not token or not chat:
        print(f"ERROR: Missing Telegram credentials for channel '{channel}'.")
        print(f"  Set {chat_env} and a bot token (TELEGRAM_BOT_TOKEN_{chan} or TELEGRAM_BOT_TOKEN) in {ENV_FILE}")
        sys.exit(1)
    return token, chat


def send_message(token: str, chat_id: str, text: str, parse_mode: str = "HTML"):
    """sendMessage. Returns {"ok": True, "result": ...} or {"ok": False, "error": ...}."""
    url = "https://api.telegram.org/bot%s/sendMessage" % token
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if payload.get("ok"):
            return {"ok": True, "result": payload.get("result", {})}
        return {"ok": False, "error": payload.get("description", "unknown error")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_photo(token: str, chat_id: str, photo_path: str, caption: str, parse_mode: str = "HTML"):
    """sendPhoto with the built message as the caption (multipart/form-data)."""
    url = "https://api.telegram.org/bot%s/sendPhoto" % token
    boundary = "----telegrampost%d" % int(datetime.now().timestamp())
    photo = Path(photo_path)
    try:
        file_bytes = photo.read_bytes()
    except Exception as e:
        return {"ok": False, "error": f"cannot read photo: {e}"}

    parts = []
    for field, value in (("chat_id", chat_id), ("caption", caption), ("parse_mode", parse_mode)):
        parts.append(("--" + boundary).encode())
        parts.append(('Content-Disposition: form-data; name="%s"' % field).encode())
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    parts.append(("--" + boundary).encode())
    parts.append(
        ('Content-Disposition: form-data; name="photo"; filename="%s"' % photo.name).encode()
    )
    parts.append(b"Content-Type: application/octet-stream")
    parts.append(b"")
    parts.append(file_bytes)
    parts.append(("--" + boundary + "--").encode())
    parts.append(b"")
    body = b"\r\n".join(parts)

    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", "multipart/form-data; boundary=%s" % boundary)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if payload.get("ok"):
            return {"ok": True, "result": payload.get("result", {})}
        return {"ok": False, "error": payload.get("description", "unknown error")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def message_link(channel: str, result: dict):
    """Best-effort t.me permalink for the sent message."""
    username = CHANNELS[channel]["username"]
    message_id = result.get("message_id")
    if username and message_id:
        return "https://t.me/%s/%s" % (username, message_id)
    return ""


def log_post(channel: str, text: str, link: str, action: str, media: bool):
    """Append the send to the JSONL log (shape mirrors the other seo logs)."""
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "channel": channel,
        "product": CHANNELS[channel]["product"],
        "action": action,
        "link": link,
        "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
        "method": "bot-api",
        "media": media,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Logged to {LOG_FILE.name}")


def record_run(link: str):
    """Call the hub's record_run.py CLI (best effort; non-fatal)."""
    if not RECORD_RUN.exists():
        return
    args = [
        sys.executable, str(RECORD_RUN),
        "--routine", "telegram-drop",
        "--category", "telegram",
        "--summary", "Telegram free->paid drop",
    ]
    if link:
        args += ["--link", "message|" + link]
    try:
        subprocess.run(args, check=False)
    except Exception as e:
        print(f"  record_run skipped: {e}")


def main():
    parser = argparse.ArgumentParser(description="Post a free->paid Telegram drop via the Bot API")
    parser.add_argument("--channel", required=True, choices=list(CHANNELS.keys()),
                        help="Target channel registry key")
    parser.add_argument("--free", required=True, help="Free-value body (shown first)")
    parser.add_argument("--tier", help="Tier CTA label (Whop/VIP/email)")
    parser.add_argument("--cta-url", dest="cta_url", help="CTA destination URL")
    parser.add_argument("--photo", help="Local image to attach (message becomes the caption)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build and lint but do not send")
    args = parser.parse_args()

    if telegram_message is None:
        print("ERROR: hub telegram_message module not importable (check the hub lib path).")
        sys.exit(1)

    cfg = CHANNELS[args.channel]
    built = telegram_message.build_message(
        free_body=args.free,
        tier=args.tier,
        cta_url=args.cta_url,
        own_domains=cfg["own_domains"],
    )

    if not built["ok"]:
        print("BLOCKED by guardrails:")
        for v in built["violations"]:
            print(f"  - {v}")
        sys.exit(3)

    text = built["text"]
    parse_mode = built["parse_mode"]
    has_media = bool(args.photo)

    if args.dry_run:
        print(f"[DRY RUN] Channel: {args.channel} ({cfg['product']})")
        print(f"[DRY RUN] parse_mode: {parse_mode}")
        if has_media:
            print(f"[DRY RUN] Photo: {args.photo}")
        print("[DRY RUN] Text:")
        print(text)
        return

    token, chat_id = get_credentials(args.channel)
    print(f"Posting to {args.channel} ({cfg['product']})...")

    if has_media:
        result = send_photo(token, chat_id, args.photo, text, parse_mode)
        action = "photo"
    else:
        result = send_message(token, chat_id, text, parse_mode)
        action = "message"

    if result["ok"]:
        link = message_link(args.channel, result["result"])
        print(f"  Sent: {link or '(no permalink)'}")
        log_post(args.channel, text, link, action, media=has_media)
        record_run(link)
    else:
        print(f"  Failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
