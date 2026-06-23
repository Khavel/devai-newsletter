"""Create one NAMED invite link per source surface for a Telegram channel.

Telegram tracks joins per invite link (member_count on getChatInviteLink), so a named link
per surface gives joins-by-source with zero UTM machinery for the Telegram hop. Run ONCE per
channel (each call to createChatInviteLink mints a NEW link); re-running mints duplicates.

Usage:
  python telegram_invite_links.py --channel fut   [--dry-run]
  python telegram_invite_links.py --channel nba

Reads the per-channel bot token + chat id from ../.env (same resolution as telegram_post.py).
Writes the results to telegram_invite_links.json (per channel) and prints them. The bot must be
an admin of the channel with can_invite_users.
"""
import argparse, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR.parent / ".env"
OUT_FILE = SCRIPT_DIR / "telegram_invite_links.json"
CHAT_ENV = {"fut": "TELEGRAM_CHAT_FUT", "nba": "TELEGRAM_CHAT_NBA", "devai": "TELEGRAM_CHAT_DEVAI"}
SURFACES = ["x-bio", "x-pinned", "yt-desc", "seo-hub", "email-welcome", "discord", "bsky"]


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    return env


def api(token, method, params):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode("utf-8"))
        except Exception: return {"ok": False, "description": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=list(CHAT_ENV.keys()))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = load_env()
    chan = a.channel.upper()
    token = env.get(f"TELEGRAM_BOT_TOKEN_{chan}") or env.get("TELEGRAM_BOT_TOKEN")
    chat = env.get(CHAT_ENV[a.channel])
    if not token or not chat:
        print(f"ERROR: missing token/chat for {a.channel} in {ENV_FILE}"); sys.exit(1)

    if a.dry_run:
        print(f"[DRY RUN] would create {len(SURFACES)} named invite links on chat {chat[:6]}... : {SURFACES}")
        return

    results = {}
    for name in SURFACES:
        r = api(token, "createChatInviteLink", {"chat_id": chat, "name": name})
        if r.get("ok"):
            link = r["result"]["invite_link"]
            results[name] = link
            print(f"  {name:14s} -> {link}")
        else:
            results[name] = {"error": r.get("description")}
            print(f"  {name:14s} -> ERROR: {r.get('description')}")

    existing = {}
    if OUT_FILE.exists():
        try: existing = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        except Exception: existing = {}
    existing[a.channel] = results
    OUT_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {OUT_FILE.name} under '{a.channel}'.")


if __name__ == "__main__":
    main()
