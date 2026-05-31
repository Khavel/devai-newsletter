"""List all posts currently on Ghost."""
import sys, json, os, time, hashlib, hmac, base64
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
ghost_url = "https://devaisemanal.com"

key_id, secret = admin_api_key.split(":", 1)
now = int(time.time())
header = json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":"))
payload = json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":"))
def b64url(d):
    return base64.urlsafe_b64encode(d).decode().rstrip("=")
h = b64url(header.encode())
p = b64url(payload.encode())
sig = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
token = f"{h}.{p}.{b64url(sig)}"

resp = httpx.get(
    f"{ghost_url}/ghost/api/admin/posts/?limit=all&fields=title,slug,status,published_at,url",
    headers={"Authorization": f"Ghost {token}", "Accept-Version": "v5.0"},
    timeout=30,
)
posts = resp.json()["posts"]
print(f"Total posts on Ghost: {len(posts)}\n")
for post in sorted(posts, key=lambda x: x.get("published_at") or ""):
    status = post["status"]
    date = (post.get("published_at") or "draft")[:10]
    slug = post["slug"]
    print(f"  [{status:>9}]  {date}  {slug}")
