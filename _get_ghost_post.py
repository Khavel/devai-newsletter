"""Fetch a single Ghost post by slug, with HTML + plaintext + published_at."""
import sys, json, os, time, hashlib, hmac, base64
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

slug = sys.argv[1] if len(sys.argv) > 1 else None
if not slug:
    print("usage: python _get_ghost_post.py <slug>")
    sys.exit(1)

admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
ghost_url = "https://devaisemanal.com"
key_id, secret = admin_api_key.split(":", 1)
now = int(time.time())
header = json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":"))
payload = json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":"))
def b64url(d):
    return base64.urlsafe_b64encode(d).decode().rstrip("=")
h = b64url(header.encode()); p = b64url(payload.encode())
sig = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
token = f"{h}.{p}.{b64url(sig)}"

resp = httpx.get(
    f"{ghost_url}/ghost/api/admin/posts/slug/{slug}/?formats=html,plaintext,mobiledoc",
    headers={"Authorization": f"Ghost {token}", "Accept-Version": "v5.0"},
    timeout=30,
)
post = resp.json()["posts"][0]
out = {
    "title": post["title"],
    "slug": post["slug"],
    "status": post["status"],
    "published_at": post.get("published_at"),
    "url": post.get("url"),
    "custom_excerpt": post.get("custom_excerpt"),
    "excerpt": (post.get("excerpt") or "")[:300],
    "feature_image": post.get("feature_image"),
    "html": post.get("html"),
    "plaintext": post.get("plaintext"),
    "tags": [t.get("name") for t in (post.get("tags") or [])],
}
# Write HTML and plaintext to files for inspection
Path("_article_html.html").write_text(out["html"] or "", encoding="utf-8")
Path("_article_plain.txt").write_text(out["plaintext"] or "", encoding="utf-8")
meta = {k: v for k, v in out.items() if k not in ("html", "plaintext")}
print(json.dumps(meta, ensure_ascii=False, indent=2))
print(f"\nHTML chars: {len(out['html'] or '')}")
print(f"Plaintext chars: {len(out['plaintext'] or '')}")
