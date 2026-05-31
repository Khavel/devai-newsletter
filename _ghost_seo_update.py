"""Update meta_title/meta_description for target low-CTR articles (CTR optimization).
Re-fetches each post's updated_at right before PUT (Ghost collision detection)."""
import sys, json, os, time, hashlib, hmac, base64
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

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

def hdr():
    return {"Authorization": f"Ghost {token()}", "Accept-Version": "v5.0", "Content-Type": "application/json"}

# (slug, meta_title, meta_description)  -- GSC low-CTR / striking-distance targets
UPDATES = [
    ("v0-dev-generar-ui-ia",
     "v0.dev: cómo funciona, precios y alternativas (2026)",
     "v0.dev de Vercel a fondo: genera componentes React/Next.js desde texto. Calidad del código, límites, precios y mejores alternativas en 2026."),
    ("github-copilot-ai-credits-pago-por-uso",
     "GitHub Copilot AI Credits: cuánto cuestan y cómo no pasarte",
     "Guía clara de los AI Credits de GitHub Copilot: qué son, cuánto cuestan las premium requests y cómo controlar el gasto del equipo sin sorpresas."),
    ("generadores-interfaces-ia-herramientas-ui",
     "Generadores de UI con IA: mejores herramientas (2026)",
     "Las mejores herramientas para generar interfaces con IA en 2026: v0.dev, Bolt y más. Cómo funcionan, precios y cuál elegir para tu proyecto."),
    ("agentes-ia-programar-guia",
     "Agentes de IA para programar: qué son y cómo funcionan (2026)",
     "Qué son los agentes de IA para programar y cómo funcionan: del autocompletado al código autónomo. Ejemplos, herramientas y límites reales en 2026."),
    ("rtk-proxy-cli-reducir-tokens-ia",
     "RTK: reduce tokens en agentes de IA sin perder errores",
     "RTK (Rust Token Killer) recorta el ruido que llega a tu modelo de IA y baja el coste en tokens. Cómo usarlo sin ocultar errores al depurar."),
    ("replit-programar-navegador-ia",
     "Replit: programar en el navegador con IA (guía 2026)",
     "Replit a fondo: IDE en el navegador con IA, deploy instantáneo y colaboración en tiempo real. Precios, límites y cuándo usarlo frente a Bolt o v0."),
]

DRY = "--apply" not in sys.argv

for slug, mt, md in UPDATES:
    r = httpx.get(f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?fields=id,updated_at,meta_title,meta_description",
                  headers=hdr(), timeout=30)
    po = r.json()["posts"][0]
    print(f"\n=== {slug} ===")
    print(f"  OLD title: {po.get('meta_title')}")
    print(f"  NEW title: {mt}  ({len(mt)} chars)")
    print(f"  OLD desc:  {po.get('meta_description')}")
    print(f"  NEW desc:  {md}  ({len(md)} chars)")
    if DRY:
        print("  [DRY RUN]")
        continue
    body = {"posts": [{"updated_at": po["updated_at"], "meta_title": mt, "meta_description": md}]}
    u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{po['id']}/", headers=hdr(), json=body, timeout=30)
    print(f"  -> PUT {u.status_code}" + ("" if u.status_code == 200 else f" :: {u.text[:200]}"))

print("\nDRY RUN (no changes). Re-run with --apply to publish." if DRY else "\nDONE.")
