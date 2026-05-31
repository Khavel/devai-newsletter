"""OAuth 2.0 PKCE token exchange helper.

Step 1: python oauth2_exchange.py generate  -> prints auth URL, saves state
Step 2: python oauth2_exchange.py exchange <redirect_url>  -> exchanges code for token
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import tweepy
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env.twitter"
TOKENS_DIR = SCRIPT_DIR / ".twitter-oauth2-tokens"
STATE_FILE = SCRIPT_DIR / ".twitter-oauth2-state.json"

load_dotenv(ENV_FILE)

CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
REDIRECT_URI = "https://localhost:3000/callback"
SCOPES = ["tweet.read", "tweet.write", "users.read", "media.write", "offline.access"]


def generate():
    oauth2 = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )
    auth_url = oauth2.get_authorization_url()

    # Save the code_verifier and state for later
    state = {
        "code_verifier": oauth2._client.code_verifier,
        "state": oauth2._state,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    print("AUTH_URL=" + auth_url)
    print("STATE_SAVED=OK")


def exchange(redirect_url, account_name):
    # Load saved state
    with open(STATE_FILE) as f:
        state = json.load(f)

    # Create a new handler and inject the saved code_verifier
    oauth2 = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )
    oauth2._client.code_verifier = state["code_verifier"]
    oauth2._state = state["state"]

    token = oauth2.fetch_token(redirect_url)
    token["expires_at"] = time.time() + token.get("expires_in", 7200)

    TOKENS_DIR.mkdir(exist_ok=True)
    token_file = TOKENS_DIR / f"{account_name.lower()}_token.json"
    with open(token_file, "w") as f:
        json.dump(token, f, indent=2)

    # Verify with httpx (tweepy has issues with OAuth 2.0 user tokens + get_me)
    import httpx
    r = httpx.get(
        "https://api.x.com/2/users/me",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    if r.status_code == 200:
        data = r.json()["data"]
        print(f"SUCCESS: Authorized as @{data['username']} (id={data['id']})")
    else:
        print(f"WARNING: Token saved but verification returned {r.status_code}: {r.text}")
    print(f"Token saved to {token_file}")
    print(f"Expires in {token.get('expires_in', '?')}s (auto-refreshes)")

    # Clean up state file
    STATE_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python oauth2_exchange.py generate")
        print("  python oauth2_exchange.py exchange <redirect_url> <account_name>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "generate":
        generate()
    elif cmd == "exchange":
        if len(sys.argv) < 4:
            print("Usage: python oauth2_exchange.py exchange <redirect_url> <account_name>")
            sys.exit(1)
        exchange(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
