"""Audit current SEO meta (meta_title/meta_description) for all Ghost posts."""
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
def b64url(d): return base64.urlsafe_b64encode(d).decode().rstrip("=")
h = b64url(json.dumps({"alg":"HS256","typ":"JWT","kid":key_id},separators=(",",":")).encode())
p = b64url(json.dumps({"iat":now,"exp":now+300,"aud":"/admin/"},separators=(",",":")).encode())
sig = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
token = f"{h}.{p}.{b64url(sig)}"

fields = "id,title,slug,status,meta_title,meta_description,custom_excerpt,updated_at,url"
resp = httpx.get(
    f"{ghost_url}/ghost/api/admin/posts/?limit=all&fields={fields}",
    headers={"Authorization": f"Ghost {token}", "Accept-Version": "v5.0"},
    timeout=30,
)
posts = resp.json()["posts"]
print(f"Total posts: {len(posts)}\n")
for po in sorted(posts, key=lambda x: x.get("slug") or ""):
    if po.get("status") != "published":
        continue
    mt = po.get("meta_title") or "(none -> uses title)"
    md = po.get("meta_description") or po.get("custom_excerpt") or "(none)"
    print(f"SLUG: {po['slug']}")
    print(f"  id:         {po['id']}")
    print(f"  title:      {po['title']}")
    print(f"  meta_title: {mt}")
    print(f"  meta_desc:  {md[:200]}")
    print(f"  updated_at: {po.get('updated_at')}")
    print()
