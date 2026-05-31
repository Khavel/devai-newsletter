"""Install a GA4 gtag snippet into devaisemanal (Ghost) via codeinjection_head.
Usage: python _ghost_set_ga.py G-XXXXXXXXXX [--apply]
Default is dry-run (prints what it would set). Idempotent: skips if the ID is already present."""
import sys, json, os, time, hashlib, hmac, base64
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

if len(sys.argv) < 2 or not sys.argv[1].upper().startswith("G-"):
    print("usage: python _ghost_set_ga.py G-XXXXXXXXXX [--apply]"); sys.exit(1)
GA_ID = sys.argv[1].upper()
APPLY = "--apply" in sys.argv

admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
GHOST = "https://devaisemanal.com"
key_id, secret = admin_api_key.split(":", 1)
def token():
    now = int(time.time())
    def b(d): return base64.urlsafe_b64encode(d).decode().rstrip("=")
    h = b(json.dumps({"alg":"HS256","typ":"JWT","kid":key_id},separators=(",",":")).encode())
    p = b(json.dumps({"iat":now,"exp":now+300,"aud":"/admin/"},separators=(",",":")).encode())
    s = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b(s)}"
def hdr(): return {"Authorization": f"Ghost {token()}", "Accept-Version":"v5.0", "Content-Type":"application/json"}

SNIPPET = (
    f'\n<!-- Google Analytics (GA4) -->\n'
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
    f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
    f'gtag("js",new Date());gtag("config","{GA_ID}");</script>\n'
)

r = httpx.get(f"{GHOST}/ghost/api/admin/settings/", headers=hdr(), timeout=30)
settings = {s["key"]: s["value"] for s in r.json()["settings"]}
current = settings.get("codeinjection_head") or ""
print(f"current codeinjection_head length: {len(current)}")
if GA_ID in current:
    print(f"SKIP: {GA_ID} already present in codeinjection_head"); sys.exit(0)
new_head = current + SNIPPET
print(f"--- will append ---\n{SNIPPET}")
if not APPLY:
    print("[DRY RUN] re-run with --apply"); sys.exit(0)
u = httpx.put(f"{GHOST}/ghost/api/admin/settings/", headers=hdr(),
              json={"settings":[{"key":"codeinjection_head","value":new_head}]}, timeout=30)
print(f"-> PUT {u.status_code}" + ("  OK" if u.status_code==200 else f" :: {u.text[:300]}"))
