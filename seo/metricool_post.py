"""Post to social networks via the Metricool API (schedule / auto-publish).

Reads METRICOOL_USER_TOKEN + METRICOOL_USER_ID from seo/.env.metricool (gitignored).
Resolves a brand by name -> blogId via /v2/settings/brands, then publishes via
/v2/scheduler/posts. F1-lint-gated (hub guardrails). Verifies the post landed, because
Metricool returns HTTP 200 even on silent failures.

MEDIA: Metricool fetches media by URL and SILENTLY DROPS expiring/private links (post
publishes with no video, no error). Use a PERMANENT public URL (Cloudflare R2 public bucket).

Usage:
  python metricool_post.py --list-brands
  python metricool_post.py --brand "NbaPropLab" --networks tiktok,youtube,instagram \
      --text "..." [--media-url https://.../clip.mp4] [--title "YT title"] \
      [--in-min 5] [--no-auto-publish] [--dry-run]
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # F1 lint (single source of truth)
except Exception:
    guardrails = None

SEO_DIR = Path(__file__).parent
ENV = SEO_DIR / ".env.metricool"
BASE = "https://app.metricool.com/api"
TZ = "Europe/Madrid"

# own-domain allowlist per brand so CTAs pass the F1 operator-link lint
OWN_DOMAINS = {
    "nbaproplab": ["nbaproplab.com", "t.me/nbaproplab_vip"],
    "futpicks": ["futpicks.com", "t.me/futpicks_vip"],
    "devaisemanal": ["devaisemanal.com"],
    "sharpyard": ["sharpyard.dev", "github.com/Khavel/dotnet-claude-starter"],
}


def load_env():
    tok = uid = None
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("METRICOOL_USER_TOKEN="):
                tok = line.split("=", 1)[1].strip()
            elif line.startswith("METRICOOL_USER_ID="):
                uid = line.split("=", 1)[1].strip()
    if not tok or not uid:
        sys.exit("ERROR: METRICOOL_USER_TOKEN / METRICOOL_USER_ID missing in .env.metricool")
    return tok, uid


def _req(method, path, token, uid, body=None, extra=""):
    url = f"{BASE}{path}?userId={uid}&integrationSource=MCP{extra}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"X-Mc-Auth": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:600]}


def get_brands(token, uid):
    s, j = _req("GET", "/v2/settings/brands", token, uid)
    return j.get("data", []) if s == 200 else []


def brand_name(b):
    return (b.get("label") or b.get("description") or "").strip()


def find_brand(brands, name):
    for b in brands:
        if brand_name(b).lower() == name.lower():
            return b
    return None


def build_payload(text, networks, media_url, title, when, auto_publish, draft=False):
    providers = [{"network": n} for n in networks]
    nd = {}
    if "instagram" in networks:
        nd["instagramData"] = {"autoPublish": True, "type": "REEL" if media_url else "POST"}
    if "youtube" in networks:
        nd["youtubeData"] = {"title": (title or text[:90]), "type": "SHORT", "madeForKids": False}
    if "tiktok" in networks:
        # TikTok direct publish REQUIRES a privacy level (no default) or it errors at publish time
        # ("does not specified privacy options"). PUBLIC_TO_EVERYONE = public (Metricool follows
        # TikTok's privacy_level_options enum). Must be a level the connected account allows.
        nd["tiktokData"] = {"privacyOption": "PUBLIC_TO_EVERYONE", "disableComments": False}
    payload = {
        "autoPublish": bool(auto_publish) and not draft,
        "draft": bool(draft),
        "text": text,
        "media": [media_url] if media_url else [],
        "mediaAltText": [""] if media_url else [],
        "providers": providers,
        "publicationDate": {"dateTime": when.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": TZ},
    }
    # Metricool stores per-network data objects at the TOP LEVEL of the post (youtubeData,
    # tiktokData, instagramData, …), NOT nested under a `networkData` key. Nesting them (as this
    # script used to) made Metricool silently drop them — which is why live YouTube publishing
    # rejected `ytTitle` as empty (the youtubeData never reached the parser). Spread them in.
    payload.update(nd)
    return payload


def main():
    p = argparse.ArgumentParser(description="Post via the Metricool API")
    p.add_argument("--list-brands", action="store_true")
    p.add_argument("--brand")
    p.add_argument("--networks", help="comma list: tiktok,youtube,instagram,linkedin,twitter,bluesky")
    p.add_argument("--text", default="")
    p.add_argument("--media-url", help="PERMANENT public URL (R2). Required for video networks.")
    p.add_argument("--title", help="YouTube title")
    p.add_argument("--in-min", type=int, default=5, help="minutes from now to publish")
    p.add_argument("--no-auto-publish", action="store_true", help="schedule (do not auto-publish)")
    p.add_argument("--draft", action="store_true", help="save as draft (never publishes)")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    token, uid = load_env()
    brands = get_brands(token, uid)

    if a.list_brands or not a.brand:
        print(f"userId={uid}  brands={len(brands)}")
        for b in brands:
            nets = list((b.get("networksData") or {}).keys())
            print(f"  blogId={b.get('id')}  name={brand_name(b)!r}  networks={nets or 'NONE CONNECTED'}")
        if not a.brand:
            return

    brand = find_brand(brands, a.brand)
    if not brand:
        sys.exit(f"ERROR: brand {a.brand!r} not found. Name a brand in Metricool first (--list-brands).")
    blog_id = brand.get("id")
    connected = [(k[:-4] if k.endswith("Data") else k) for k in (brand.get("networksData") or {}).keys()]
    networks = [n.strip() for n in (a.networks or "").split(",") if n.strip()]
    if not networks:
        sys.exit("ERROR: --networks required")
    missing = [n for n in networks if n not in connected]
    if missing:
        sys.exit(f"ERROR: {missing} not connected to brand {a.brand!r} (connected: {connected or 'none'}). "
                 "Connect them in the Metricool UI (OAuth) first.")

    # F1 lint
    if guardrails is not None:
        own = OWN_DOMAINS.get(a.brand.lower(), [])
        violations = guardrails.lint_text(a.text, own_domains=own)
        if violations:
            print("BLOCKED by guardrails:")
            for v in violations:
                print(f"  - {v}")
            sys.exit(3)

    when = datetime.now() + timedelta(minutes=max(1, a.in_min))
    payload = build_payload(a.text, networks, a.media_url, a.title, when,
                            not a.no_auto_publish, draft=a.draft)

    if a.dry_run:
        print(f"[DRY RUN] brand={a.brand} blogId={blog_id} networks={networks}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    s, j = _req("POST", "/v2/scheduler/posts", token, uid, body=payload, extra=f"&blogId={blog_id}")
    if s not in (200, 201):
        sys.exit(f"POST failed {s}: {j}")
    post_id = (j.get("data") or {}).get("id") or j.get("id")
    print(f"  scheduled/published (id={post_id}, blogId={blog_id}, networks={networks})")

    # verify (Metricool returns 200 even on silent failures)
    sv, jv = _req("GET", "/v2/scheduler/posts", token, uid, extra=f"&blogId={blog_id}")
    ok = any(str((it.get('id'))) == str(post_id) for it in (jv.get("data") or [])) if sv == 200 else False
    print(f"  verify: {'CONFIRMED in scheduler' if ok else 'NOT FOUND - check Metricool UI'}")


if __name__ == "__main__":
    main()
