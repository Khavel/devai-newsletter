"""Check indexing status for all URLs across both sites via GSC URL Inspection API."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)

from src.seo_intelligence import get_gsc_access_token
import httpx

token = get_gsc_access_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"

SITES = {
    "https://devaisemanal.com/": [
        "/", "/claude-code-que-es-guia-completa/", "/cursor-ai-que-es-guia-completa/",
        "/github-copilot-guia-completa/", "/tabnine-autocompletado-codigo-ia/",
        "/windsurf-ide-editor-ia/", "/replit-programar-navegador-ia/",
        "/v0-dev-generar-ui-ia/", "/bolt-new-crear-apps-ia-navegador/",
        "/amazon-q-developer-ia-aws/", "/vs-code-copilot-coauthored-by-commits/",
        "/zed-parallel-agents-editor-ia/", "/rtk-proxy-cli-reducir-tokens-ia/",
        "/serena-mcp-busqueda-semantica-codigo/", "/github-copilot-datos-entrenamiento-privacidad/",
        "/copilot-code-review-minutos-github-actions/", "/github-copilot-ai-credits-pago-por-uso/",
        "/newsletter-2026-05-19/", "/newsletter-2026-05-12/", "/newsletter-2026-05-05/",
        "/newsletter-2026-04-28/", "/newsletter-2026-04-21/", "/newsletter-2026-04-14/",
        "/newsletter-2026-04-07/", "/newsletter-2026-03-31/", "/newsletter-2026-03-29/",
    ],
    "sc-domain:tpv-top.com": [
        "/", "/precios", "/tpv-hosteleria", "/tpv-verifactu", "/tpv-sin-internet",
        "/pantalla-cocina-kds", "/contacto", "/demo/tpv", "/descargar", "/soporte",
        "/blog/verifactu-obligatorio-tpv-restaurante", "/blog/verifactu-aplazado-2027-restaurantes",
    ],
}

results = {"indexed": [], "not_indexed": []}

with httpx.Client(timeout=30) as c:
    for site_url, paths in SITES.items():
        base = "https://tpv-top.com" if "tpv-top" in site_url else "https://devaisemanal.com"
        site_label = "tpv-top.com" if "tpv-top" in site_url else "devaisemanal.com"
        print(f"\n{'='*60}", flush=True)
        print(f" {site_label}", flush=True)
        print(f"{'='*60}", flush=True)

        for path in paths:
            full_url = base + path
            try:
                r = c.post(API, json={"inspectionUrl": full_url, "siteUrl": site_url}, headers=headers)
                data = r.json()
                idx = data.get("inspectionResult", {}).get("indexStatusResult", {})
                verdict = idx.get("verdict", "?")
                coverage = idx.get("coverageState", "?")
                crawled = idx.get("lastCrawlTime", "never")
                crawl_date = crawled[:10] if crawled and crawled != "never" else "never"

                if verdict == "PASS":
                    status = "OK"
                    results["indexed"].append(full_url)
                else:
                    status = "MISS"
                    results["not_indexed"].append((full_url, site_url, coverage))

                print(f"  {status:4s} | {path:55s} | {coverage:30s} | {crawl_date}", flush=True)
            except Exception as e:
                print(f"  ERR  | {path:55s} | {e}", flush=True)

print(f"\n{'='*60}", flush=True)
print(f"SUMMARY", flush=True)
print(f"  Indexed:     {len(results['indexed'])}", flush=True)
print(f"  Not indexed: {len(results['not_indexed'])}", flush=True)
if results["not_indexed"]:
    print(f"\nURLs needing indexing:", flush=True)
    for url, site, reason in results["not_indexed"]:
        print(f"  - {url}  ({reason})", flush=True)
