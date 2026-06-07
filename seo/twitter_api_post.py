"""Post tweets via official X/Twitter API using tweepy.

Usage:
  python twitter_api_post.py --account FutProbLab "Your tweet text here"
  python twitter_api_post.py --account FutProbLab --file tweet_draft.txt
  python twitter_api_post.py --account FutProbLab "Reply text" --reply-to 1234567890

Accounts:
  - FutProbLab: Uses OAuth 1.0a (direct access tokens from developer console)
  - DevAISemanal / StatLineNerd: Uses OAuth 2.0 PKCE (requires initial auth flow)

Cost: ~$0.015/text tweet, ~$0.20/tweet with URL (pay-per-use)
"""
import argparse
import json
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path

# Reuse the hub's guardrails (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # type: ignore
except Exception:
    guardrails = None

# Fix Windows console encoding for emoji output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
import tweepy
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env.twitter"
LOG_FILE = SCRIPT_DIR / "twitter_post_log.jsonl"
TOKENS_DIR = SCRIPT_DIR / ".twitter-oauth2-tokens"

# Account metadata
ACCOUNTS = {
    "FutProbLab": {
        "handle": "@FutProbLab",
        "product": "FutPicks",
        "auth": "oauth1",  # Direct access tokens from dev console
    },
    "DevAISemanal": {
        "handle": "@DevAISemanal",
        "product": "DevAI Semanal",
        "auth": "oauth2",  # Needs OAuth 2.0 PKCE
    },
    "StatLineNerd": {
        "handle": "@StatLineNerd",
        "product": "NbaPropLab",
        "auth": "oauth2",  # Needs OAuth 2.0 PKCE
    },
}


def load_env():
    """Load Twitter API credentials from .env.twitter file."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    else:
        print(f"ERROR: {ENV_FILE} not found. Run the developer console setup first.")
        sys.exit(1)


def get_oauth1_client(account: str) -> tweepy.Client:
    """Get a tweepy Client using OAuth 1.0a (for @FutProbLab)."""
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv(f"{account.upper()}_ACCESS_TOKEN")
    access_secret = os.getenv(f"{account.upper()}_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print(f"ERROR: Missing OAuth 1.0a credentials for {account}")
        print("Check .env.twitter file")
        sys.exit(1)

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )


def get_oauth2_client(account: str) -> tweepy.Client:
    """Get a tweepy Client using OAuth 2.0 PKCE (for DevAISemanal, StatLineNerd).

    Requires running the auth flow first:
      python twitter_api_post.py --account DevAISemanal --auth
    """
    TOKENS_DIR.mkdir(exist_ok=True)
    token_file = TOKENS_DIR / f"{account.lower()}_token.json"

    if not token_file.exists():
        print(f"ERROR: No OAuth 2.0 token for {account}.")
        print(f"Run: python {__file__} --account {account} --auth")
        sys.exit(1)

    with open(token_file) as f:
        token_data = json.load(f)

    client_id = os.getenv("TWITTER_CLIENT_ID")
    client_secret = os.getenv("TWITTER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: Missing TWITTER_CLIENT_ID or TWITTER_CLIENT_SECRET")
        sys.exit(1)

    # Check if token needs refresh
    if token_data.get("expires_at", 0) < time.time():
        print(f"  Refreshing OAuth 2.0 token for {account}...")
        oauth2 = tweepy.OAuth2UserHandler(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="https://localhost:3000/callback",
            scope=["tweet.read", "tweet.write", "users.read", "media.write", "offline.access"],
        )
        try:
            new_token = oauth2.refresh_token(
                "https://api.x.com/2/oauth2/token",
                refresh_token=token_data["refresh_token"],
                client_id=client_id,
                client_secret=client_secret,
            )
            new_token["expires_at"] = time.time() + new_token.get("expires_in", 7200)
            with open(token_file, "w") as f:
                json.dump(new_token, f, indent=2)
            token_data = new_token
            print("  Token refreshed OK")
        except Exception as e:
            print(f"  Token refresh failed: {e}")
            print(f"  Re-run: python {__file__} --account {account} --auth")
            sys.exit(1)

    # For OAuth 2.0 user tokens, we wrap the access token in a simple object
    # that the post_tweet function can detect and handle with httpx
    class OAuth2Token:
        def __init__(self, access_token):
            self.access_token = access_token
            self._is_oauth2 = True
    return OAuth2Token(token_data["access_token"])


def do_oauth2_auth(account: str):
    """Interactive OAuth 2.0 PKCE authorization flow.

    Opens a browser for the user to authorize the app, then saves
    the access/refresh token pair for future use.
    """
    load_env()
    client_id = os.getenv("TWITTER_CLIENT_ID")
    client_secret = os.getenv("TWITTER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: Missing TWITTER_CLIENT_ID or TWITTER_CLIENT_SECRET")
        sys.exit(1)

    TOKENS_DIR.mkdir(exist_ok=True)

    oauth2 = tweepy.OAuth2UserHandler(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="https://localhost:3000/callback",
        scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
    )

    auth_url = oauth2.get_authorization_url()
    print(f"\n{'='*60}")
    print(f"OAuth 2.0 Authorization for {ACCOUNTS[account]['handle']}")
    print(f"{'='*60}")
    print(f"\n1. Log into Twitter as {ACCOUNTS[account]['handle']}")
    print(f"2. Open this URL in your browser:\n")
    print(f"   {auth_url}\n")
    print(f"3. Authorize the app")
    print(f"4. You'll be redirected to localhost (it will fail to load)")
    print(f"5. Copy the FULL redirect URL from your browser's address bar")
    print(f"   (it looks like: https://localhost:3000/callback?state=...&code=...)")
    print(f"\nPaste the redirect URL here:")

    redirect_url = input("> ").strip()

    try:
        token = oauth2.fetch_token(redirect_url)
        token["expires_at"] = time.time() + token.get("expires_in", 7200)

        token_file = TOKENS_DIR / f"{account.lower()}_token.json"
        with open(token_file, "w") as f:
            json.dump(token, f, indent=2)

        # Verify by getting user info
        client = tweepy.Client(token["access_token"])
        me = client.get_me()
        print(f"\n✅ Authorized as @{me.data.username}")
        print(f"   Token saved to {token_file}")
        print(f"   Token expires in {token.get('expires_in', '?')}s (auto-refreshes)")
    except Exception as e:
        print(f"\n❌ Authorization failed: {e}")
        sys.exit(1)


def resolve_image(image: str = None, image_url: str = None, pick_id: int = None) -> str:
    """Return a local path to the image to attach.

    - image:     a local file path (used as-is)
    - image_url: an http(s) URL — downloaded to a temp file
    - pick_id:   an NbaPropLab pick id — resolves to the public pick-card PNG
    Returns the local path, or None if nothing was provided.
    """
    if image:
        if not Path(image).exists():
            raise FileNotFoundError(f"image not found: {image}")
        return image

    if pick_id and not image_url:
        image_url = f"https://nbaproplab.com/api/v1/screenshots/pick/{pick_id}.png"

    if image_url:
        r = httpx.get(image_url, timeout=60, follow_redirects=True)
        if r.status_code != 200:
            raise RuntimeError(f"image download failed {r.status_code}: {image_url}")
        suffix = ".png" if ".png" in image_url.lower() else ".jpg"
        tmp = SCRIPT_DIR / f".tmp_media{suffix}"
        tmp.write_bytes(r.content)
        return str(tmp)

    return None


def _guess_mime(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".gif"):
        return "image/gif"
    if p.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def upload_media_oauth2(access_token: str, image_path: str) -> str:
    """Upload an image via the X API v2 media endpoint (requires media.write scope).

    Returns the media id string. Uses the simple (single-request) multipart upload,
    which is fine for static images well under the 5 MB limit (our cards are ~200 KB).
    """
    with open(image_path, "rb") as fh:
        files = {"media": (os.path.basename(image_path), fh, _guess_mime(image_path))}
        data = {"media_category": "tweet_image"}
        r = httpx.post(
            "https://api.x.com/2/media/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
            data=data,
            timeout=120,
        )
    if r.status_code in (200, 201):
        j = r.json()
        media_id = (
            (j.get("data") or {}).get("id")
            or j.get("media_id_string")
            or j.get("id")
        )
        if not media_id:
            raise RuntimeError(f"media upload OK but no media id in response: {j}")
        return str(media_id)
    raise RuntimeError(f"media upload failed {r.status_code}: {r.text}")


def upload_media_oauth1(account: str, image_path: str) -> str:
    """Upload an image via the v1.1 media endpoint using OAuth 1.0a (for @FutProbLab)."""
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv(f"{account.upper()}_ACCESS_TOKEN")
    access_secret = os.getenv(f"{account.upper()}_ACCESS_TOKEN_SECRET")
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)
    media = api.media_upload(filename=image_path)
    return str(media.media_id_string)


def post_tweet(client, text: str, reply_to: str = None, media_ids: list = None) -> dict:
    """Post a tweet and return result dict.

    Supports both tweepy.Client (OAuth 1.0a) and OAuth2Token (OAuth 2.0 PKCE).
    Optionally attaches already-uploaded media via media_ids.
    """
    if reply_to and "/" in reply_to:
        reply_to = reply_to.rstrip("/").split("/")[-1]

    # OAuth 2.0 user token — use httpx directly
    if hasattr(client, "_is_oauth2"):
        try:
            payload = {"text": text}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}
            if media_ids:
                payload["media"] = {"media_ids": [str(m) for m in media_ids]}
            r = httpx.post(
                "https://api.x.com/2/tweets",
                json=payload,
                headers={"Authorization": f"Bearer {client.access_token}"},
            )
            if r.status_code in (200, 201):
                tweet_id = r.json()["data"]["id"]
                return {"ok": True, "tweet_id": tweet_id}
            else:
                return {"ok": False, "error": f"{r.status_code}: {r.text}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # OAuth 1.0a — use tweepy
    try:
        kwargs = {"text": text}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to
        if media_ids:
            kwargs["media_ids"] = [str(m) for m in media_ids]
        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        return {"ok": True, "tweet_id": tweet_id}
    except tweepy.errors.TweepyException as e:
        return {"ok": False, "error": str(e)}


def log_tweet(account: str, tweet_id: str, text: str, action: str = "tweet", media: bool = False):
    """Append tweet to the JSONL log."""
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "account": account,
        "handle": ACCOUNTS[account]["handle"],
        "product": ACCOUNTS[account]["product"],
        "action": action,
        "tweet_id": str(tweet_id),
        "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
        "method": "api",
        "media": media,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Logged to {LOG_FILE.name}")


def main():
    parser = argparse.ArgumentParser(description="Post tweets via official X API")
    parser.add_argument("text", nargs="?", help="Tweet text (or use --file)")
    parser.add_argument("--account", "-a", required=True,
                        choices=list(ACCOUNTS.keys()),
                        help="Twitter account to post from")
    parser.add_argument("--file", "-f", help="Read tweet text from file")
    parser.add_argument("--reply-to", help="Tweet ID or URL to reply to")
    parser.add_argument("--image", help="Local image path to attach")
    parser.add_argument("--image-url", help="Image URL to download and attach")
    parser.add_argument("--pick-id", type=int,
                        help="NbaPropLab pick id -> attaches its public card PNG")
    parser.add_argument("--auth", action="store_true",
                        help="Run OAuth 2.0 authorization flow")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print tweet but don't post")
    args = parser.parse_args()

    # OAuth 2.0 auth flow
    if args.auth:
        if ACCOUNTS[args.account]["auth"] != "oauth2":
            print(f"{args.account} uses OAuth 1.0a (direct tokens). No auth flow needed.")
            sys.exit(0)
        do_oauth2_auth(args.account)
        return

    # Get tweet text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text
    else:
        print("ERROR: Provide tweet text as argument or --file")
        sys.exit(1)

    if not text:
        print("ERROR: Tweet text is empty")
        sys.exit(1)

    if len(text) > 280:
        print(f"WARNING: Tweet is {len(text)} chars (max 280).")

    OWN_DOMAINS = {
        "StatLineNerd": ["nbaproplab.com", "t.me/nbaproplab_vip"],
        "FutProbLab": ["futpicks.com", "t.me/futpicks_vip",
                       "futpicks.substack.com", "tipstrr.com/tipster/futpicks",
                       "blogabet.com/futpicks"],
        "DevAISemanal": ["devaisemanal.com"],
    }
    if guardrails is not None:
        violations = guardrails.lint_text(text, own_domains=OWN_DOMAINS.get(args.account, []))
        if violations:
            print("BLOCKED by guardrails:")
            for v in violations:
                print(f"  - {v}")
            sys.exit(3)

    has_media = bool(args.image or args.image_url or args.pick_id)

    # Dry run
    if args.dry_run:
        print(f"[DRY RUN] Account: {ACCOUNTS[args.account]['handle']}")
        print(f"[DRY RUN] Text ({len(text)} chars):")
        print(text)
        if has_media:
            src = args.image or args.image_url or f"pick-card #{args.pick_id}"
            print(f"[DRY RUN] Media: {src}")
        return

    # Load credentials and get client
    load_env()
    account_cfg = ACCOUNTS[args.account]

    print(f"Posting as {account_cfg['handle']} ({account_cfg['product']})...")
    print(f"  Auth method: {account_cfg['auth']}")

    if account_cfg["auth"] == "oauth1":
        client = get_oauth1_client(args.account)
    else:
        client = get_oauth2_client(args.account)

    # Resolve + upload media (if any)
    media_ids = None
    if has_media:
        try:
            image_path = resolve_image(args.image, args.image_url, args.pick_id)
            print(f"  Uploading media: {image_path}")
            if account_cfg["auth"] == "oauth1":
                media_id = upload_media_oauth1(args.account, image_path)
            else:
                media_id = upload_media_oauth2(client.access_token, image_path)
            media_ids = [media_id]
            print(f"  Media uploaded (id={media_id})")
        except Exception as e:
            print(f"  ❌ Media upload failed: {e}")
            sys.exit(1)

    # Post
    action = "reply" if args.reply_to else "tweet"
    result = post_tweet(client, text, args.reply_to, media_ids=media_ids)

    if result["ok"]:
        tweet_id = result["tweet_id"]
        url = f"https://x.com/{account_cfg['handle'].lstrip('@')}/status/{tweet_id}"
        print(f"  ✅ Posted: {url}")
        log_tweet(args.account, tweet_id, text, action, media=bool(media_ids))
    else:
        print(f"  ❌ Failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
