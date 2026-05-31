"""Submit newly published URLs for indexing via GSC URL Inspection API."""
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

NEW_URLS = [
    # Guías evergreen (recién publicadas — SEO expansion)
    "https://devaisemanal.com/guias-claude-code/",
    "https://devaisemanal.com/guias-mcp-servers/",
    "https://devaisemanal.com/guias-vibe-coding/",
    "https://devaisemanal.com/tutoriales-claude-code-aceptar-automaticamente/",
    "https://devaisemanal.com/tutoriales-claude-code-hooks/",
    "https://devaisemanal.com/comparativas-claude-sonnet-opus-haiku/",
    "https://devaisemanal.com/comparativas-claude-code-vs-cursor/",
    # Posts anteriores
    "https://devaisemanal.com/generadores-interfaces-ia-herramientas-ui/",
    "https://devaisemanal.com/amazon-codewhisperer-vs-q-developer-ia-aws/",
    "https://devaisemanal.com/claude-code-terminal-ia-guia/",
    "https://devaisemanal.com/mejores-editores-codigo-ia-2026/",
    "https://devaisemanal.com/mcp-model-context-protocol-guia/",
    "https://devaisemanal.com/agentes-ia-programar-guia/",
]

print("Checking index status of new URLs...\n")
for url in NEW_URLS:
    body = {"inspectionUrl": url, "siteUrl": "https://devaisemanal.com/"}
    resp = httpx.post(API, headers=headers, json=body, timeout=30)
    data = resp.json()
    result = data.get("inspectionResult", {})
    index_status = result.get("indexStatusResult", {})
    verdict = index_status.get("verdict", "?")
    coverage = index_status.get("coverageState", "?")
    crawl_time = index_status.get("lastCrawlTime", "never")[:10] if index_status.get("lastCrawlTime") else "never"

    slug = url.replace("https://devaisemanal.com/", "").rstrip("/")
    status = "OK" if verdict == "PASS" else "MISS"
    print(f"  {status:>4}  | /{slug:<55} | {coverage:<35} | {crawl_time}")

print("\nNote: Google deprecated the /ping?sitemap= endpoint (June 2023).")
print("To speed up indexing, manually request it in Search Console:")
print("  → URL Inspection → paste URL → Request Indexing")
print("Ghost auto-includes new pages in /sitemap.xml — Googlebot will discover them within days.")
