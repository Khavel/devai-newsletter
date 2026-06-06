"""Post to Bluesky via the atproto API (app password auth).

Usage:
  python bluesky_post.py --account DevAISemanal "Your post text here"
  python bluesky_post.py --account DevAISemanal --file post_draft.txt
  python bluesky_post.py --account DevAISemanal "Reply text" --reply-to at://did/app.bsky.feed.post/abc
  python bluesky_post.py --account DevAISemanal "Look at this" --image card.png
  python bluesky_post.py --account DevAISemanal "text" --dry-run

Accounts are defined in ACCOUNTS below; credentials (handle + app password) come
from seo/.env.bluesky (NEVER committed). Modeled on twitter_api_post.py: the pure
record builder + operator lint both live in the hub and are imported via the shim.

Bluesky is a separate platform with separate identities, so it is exempt from the
X 3-account anti-detection rules, but it still goes through the operator lint.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reuse the hub's pure builder + guardrails (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # type: ignore
except Exception:
    guardrails = None
try:
    import bluesky_record  # type: ignore
except Exception:
    bluesky_record = None

# Fix Windows console encoding for non-ascii output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env.bluesky"
LOG_FILE = SCRIPT_DIR / "bluesky_post_log.jsonl"

# Account metadata. handle/app_password come from env vars (see .env.bluesky):
#   <ENV_PREFIX>_HANDLE        e.g. DEVAISEMANAL_BSKY_HANDLE
#   <ENV_PREFIX>_APP_PASSWORD  e.g. DEVAISEMANAL_BSKY_APP_PASSWORD
ACCOUNTS = {
    "DevAISemanal": {
        "handle_env": "DEVAISEMANAL_BSKY_HANDLE",
        "app_password_env": "DEVAISEMANAL_BSKY_APP_PASSWORD",
        "product": "DevAI Semanal",
        "own_domains": ["devaisemanal.com"],
    },
    "FutProbLab": {
        "handle_env": "FUTPROBLAB_BSKY_HANDLE",
        "app_password_env": "FUTPROBLAB_BSKY_APP_PASSWORD",
        "product": "FutPicks",
        "own_domains": ["futpicks.com", "t.me/futpicks_vip"],
    },
    "StatLineNerd": {
        "handle_env": "STATLINENERD_BSKY_HANDLE",
        "app_password_env": "STATLINENERD_BSKY_APP_PASSWORD",
        "product": "NbaPropLab",
        "own_domains": ["nbaproplab.com", "t.me/nbaproplab_vip"],
    },
    "Sharpyard": {
        "handle_env": "SHARPYARD_BSKY_HANDLE",
        "app_password_env": "SHARPYARD_BSKY_APP_PASSWORD",
        "product": "Sharpyard",
        "own_domains": ["sharpyard.com"],
    },
}


def load_env():
    """Load Bluesky credentials from .env.bluesky."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    else:
        print(f"ERROR: {ENV_FILE} not found. Create it with per-account handle + app password.")
        sys.exit(1)


def get_credentials(account: str):
    """Return (handle, app_password) for an account or exit if missing."""
    cfg = ACCOUNTS[account]
    handle = os.getenv(cfg["handle_env"])
    app_password = os.getenv(cfg["app_password_env"])
    if not handle or not app_password:
        print(f"ERROR: Missing Bluesky credentials for {account}.")
        print(f"  Set {cfg['handle_env']} and {cfg['app_password_env']} in {ENV_FILE.name}")
        sys.exit(1)
    return handle, app_password


def resolve_image(image: str = None, image_url: str = None) -> str:
    """Return a local path to the image to attach (or None)."""
    if image:
        if not Path(image).exists():
            raise FileNotFoundError(f"image not found: {image}")
        return image
    if image_url:
        r = httpx.get(image_url, timeout=60, follow_redirects=True)
        if r.status_code != 200:
            raise RuntimeError(f"image download failed {r.status_code}: {image_url}")
        suffix = ".png" if ".png" in image_url.lower() else ".jpg"
        tmp = SCRIPT_DIR / f".tmp_bsky_media{suffix}"
        tmp.write_bytes(r.content)
        return str(tmp)
    return None


def _parse_reply(reply_to: str):
    """Build the reply dict the pure builder expects.

    Bluesky needs strong refs (uri + cid) for both root and parent. We resolve
    them from the parent post's thread so a single at:// uri is enough.
    """
    if not reply_to:
        return None, None
    return reply_to, None


def post_to_bluesky(account: str, text: str, reply_to: str = None,
                    image_path: str = None, image_alt: str = None) -> dict:
    """Login, optionally upload an image, and create the post.

    Returns {"ok": True, "uri": ..., "cid": ...} or {"ok": False, "error": ...}.
    Wraps everything so a failure never tracebacks.
    """
    try:
        from atproto import Client, models  # atproto import stays inside the live client

        handle, app_password = get_credentials(account)
        client = Client()
        client.login(handle, app_password)
        did = client.me.did

        # Resolve reply strong refs from the parent thread (uri -> {uri, cid}).
        reply = None
        if reply_to:
            thread = client.get_post_thread(reply_to)
            parent_post = thread.thread.post
            parent_ref = {"uri": parent_post.uri, "cid": parent_post.cid}
            root_ref = parent_ref
            parent_reply = getattr(parent_post.record, "reply", None)
            if parent_reply is not None and getattr(parent_reply, "root", None) is not None:
                root_ref = {"uri": parent_reply.root.uri, "cid": parent_reply.root.cid}
            reply = {"root": root_ref, "parent": parent_ref}

        # Build the pure record (text clean, 300-grapheme cap, createdAt, reply dict).
        rec = bluesky_record.build_post_record(
            text, embed_alt=image_alt if image_path else None, reply=reply
        )

        # Upload the image blob and build the real images embed (swaps _embed_alt).
        embed = None
        if image_path:
            with open(image_path, "rb") as fh:
                blob = client.upload_blob(fh.read()).blob
            alt = bluesky_record._clean(image_alt or "")
            embed = models.AppBskyEmbedImages.Main(
                images=[models.AppBskyEmbedImages.Image(alt=alt, image=blob)]
            )

        # Map the pure dict into the atproto Record model.
        reply_ref = None
        if rec.get("reply"):
            r = rec["reply"]
            reply_ref = models.AppBskyFeedPost.ReplyRef(
                parent=models.ComAtprotoRepoStrongRef.Main(
                    uri=r["parent"]["uri"], cid=r["parent"]["cid"]
                ),
                root=models.ComAtprotoRepoStrongRef.Main(
                    uri=r["root"]["uri"], cid=r["root"]["cid"]
                ),
            )
        record = models.AppBskyFeedPost.Record(
            text=rec["text"],
            created_at=rec["createdAt"],
            reply=reply_ref,
            embed=embed,
        )

        resp = client.app.bsky.feed.post.create(did, record)
        return {"ok": True, "uri": resp.uri, "cid": resp.cid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def log_post(account: str, uri: str, text: str, action: str = "post", media: bool = False):
    """Append the post to the JSONL log (same shape as the twitter log)."""
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "account": account,
        "handle": os.getenv(ACCOUNTS[account]["handle_env"], account),
        "product": ACCOUNTS[account]["product"],
        "action": action,
        "uri": str(uri),
        "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
        "method": "atproto",
        "media": media,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Logged to {LOG_FILE.name}")


def main():
    parser = argparse.ArgumentParser(description="Post to Bluesky via atproto")
    parser.add_argument("text", nargs="?", help="Post text (or use --file)")
    parser.add_argument("--account", "-a", required=True,
                        choices=list(ACCOUNTS.keys()),
                        help="Bluesky account to post from")
    parser.add_argument("--file", "-f", help="Read post text from file")
    parser.add_argument("--reply-to", help="Parent post at:// uri to reply to")
    parser.add_argument("--image", help="Local image path to attach")
    parser.add_argument("--image-url", help="Image URL to download and attach")
    parser.add_argument("--image-alt", default="", help="Alt text for the attached image")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the post but do not send it")
    args = parser.parse_args()

    if bluesky_record is None:
        print("ERROR: hub bluesky_record module not importable (check the hub lib path).")
        sys.exit(1)

    # Resolve text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text
    else:
        print("ERROR: Provide post text as argument or --file")
        sys.exit(1)

    if not text:
        print("ERROR: Post text is empty")
        sys.exit(1)

    # Operator lint (same as F1.4): exit 3 on any violation, dry-run included.
    cfg = ACCOUNTS[args.account]
    if guardrails is not None:
        violations = guardrails.lint_text(text, own_domains=cfg["own_domains"])
        if violations:
            print("BLOCKED by guardrails:")
            for v in violations:
                print(f"  - {v}")
            sys.exit(3)

    has_media = bool(args.image or args.image_url)

    # Validate against the 300-grapheme cap up front (pure builder is the gate).
    try:
        bluesky_record.build_post_record(text)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Dry run
    if args.dry_run:
        print(f"[DRY RUN] Account: {args.account} ({cfg['product']})")
        print(f"[DRY RUN] Text ({len(text)} chars):")
        print(text)
        if args.reply_to:
            print(f"[DRY RUN] Reply to: {args.reply_to}")
        if has_media:
            src = args.image or args.image_url
            print(f"[DRY RUN] Media: {src} (alt: {args.image_alt or '<none>'})")
        return

    load_env()
    print(f"Posting as {args.account} ({cfg['product']})...")

    # Resolve media (download if a URL)
    image_path = None
    if has_media:
        try:
            image_path = resolve_image(args.image, args.image_url)
            print(f"  Attaching media: {image_path}")
        except Exception as e:
            print(f"  Media resolve failed: {e}")
            sys.exit(1)

    action = "reply" if args.reply_to else "post"
    result = post_to_bluesky(
        args.account, text, reply_to=args.reply_to,
        image_path=image_path, image_alt=args.image_alt,
    )

    if result["ok"]:
        uri = result["uri"]
        print(f"  Posted: {uri}")
        log_post(args.account, uri, text, action, media=has_media)
    else:
        print(f"  Failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
