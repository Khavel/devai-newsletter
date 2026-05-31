"""Add an 'Artículos relacionados' internal-link cluster to key articles.
Safe method: append ONE self-contained Ghost HTML-card node to the post's lexical
(does not touch existing content). Idempotent + inserts before a trailing CTA card."""
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
def hdr(): return {"Authorization": f"Ghost {token()}", "Accept-Version":"v5.0", "Content-Type":"application/json"}

A = {  # slug -> readable anchor
 "bolt-new-crear-apps-ia-navegador":"Bolt.new: crear apps con IA",
 "generadores-interfaces-ia-herramientas-ui":"Generadores de UI con IA",
 "replit-programar-navegador-ia":"Replit: programar con IA en el navegador",
 "mejores-editores-codigo-ia-2026":"Los mejores editores de código con IA",
 "cursor-ai-que-es-guia-completa":"Cursor AI: guía completa",
 "v0-dev-generar-ui-ia":"v0.dev: generar UI con IA",
 "github-copilot-guia-completa":"GitHub Copilot: guía completa",
 "github-copilot-datos-entrenamiento-privacidad":"GitHub Copilot y privacidad",
 "copilot-code-review-minutos-github-actions":"Copilot Code Review y GitHub Actions",
 "windsurf-ide-editor-ia":"Windsurf IDE",
 "claude-code-que-es-guia-completa":"Qué es Claude Code",
 "mcp-model-context-protocol-guia":"MCP (Model Context Protocol)",
 "hooks-agentes-codigo-guardrails-validacion":"Hooks para agentes de código",
 "serena-mcp-busqueda-semantica-codigo":"Serena MCP",
 "rtk-proxy-cli-reducir-tokens-ia":"RTK: reducir tokens en IA",
 "real-time-chunking-rag-streaming":"Real-time chunking para RAG",
}
CLUSTER = {  # target slug -> related slugs
 "v0-dev-generar-ui-ia":["bolt-new-crear-apps-ia-navegador","generadores-interfaces-ia-herramientas-ui","replit-programar-navegador-ia","mejores-editores-codigo-ia-2026"],
 "replit-programar-navegador-ia":["bolt-new-crear-apps-ia-navegador","v0-dev-generar-ui-ia","cursor-ai-que-es-guia-completa","mejores-editores-codigo-ia-2026"],
 "generadores-interfaces-ia-herramientas-ui":["v0-dev-generar-ui-ia","bolt-new-crear-apps-ia-navegador","replit-programar-navegador-ia"],
 "tabnine-autocompletado-codigo-ia":["github-copilot-guia-completa","cursor-ai-que-es-guia-completa","windsurf-ide-editor-ia","mejores-editores-codigo-ia-2026"],
 "github-copilot-ai-credits-pago-por-uso":["github-copilot-guia-completa","github-copilot-datos-entrenamiento-privacidad","copilot-code-review-minutos-github-actions"],
 "agentes-ia-programar-guia":["claude-code-que-es-guia-completa","mcp-model-context-protocol-guia","hooks-agentes-codigo-guardrails-validacion","mejores-editores-codigo-ia-2026"],
 "rtk-proxy-cli-reducir-tokens-ia":["serena-mcp-busqueda-semantica-codigo","mcp-model-context-protocol-guia","real-time-chunking-rag-streaming"],
 "serena-mcp-busqueda-semantica-codigo":["mcp-model-context-protocol-guia","rtk-proxy-cli-reducir-tokens-ia","claude-code-que-es-guia-completa"],
}
def related_html(slugs):
    lis = "".join(f'<li><a href="{GHOST}/{s}/">{A[s]}</a></li>' for s in slugs)
    return (f'<h2 id="articulos-relacionados">Artículos relacionados</h2><ul>{lis}</ul>')

DRY = "--apply" not in sys.argv
only = [a for a in sys.argv[1:] if not a.startswith("--")]

for slug, rel in CLUSTER.items():
    if only and slug not in only: continue
    r = httpx.get(f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?formats=lexical&fields=id,updated_at,lexical", headers=hdr(), timeout=30)
    po = r.json()["posts"][0]
    lex = json.loads(po["lexical"])
    kids = lex["root"]["children"]
    types = [c.get("type") for c in kids]
    if "articulos-relacionados" in po["lexical"]:
        print(f"SKIP {slug}: related section already present"); continue
    node = {"type":"html","html":related_html(rel),"version":1}
    # insert before the trailing run of html (CTA) cards, so it sits after the body
    pos = len(kids)
    while pos > 0 and kids[pos-1].get("type") == "html":
        pos -= 1
    print(f"\n=== {slug} ===")
    print(f"  child types: {types}")
    print(f"  inserting related-links html-card at index {pos} of {len(kids)} -> links: {rel}")
    if DRY:
        print("  [DRY RUN]"); continue
    kids.insert(pos, node)
    body = {"posts":[{"updated_at":po["updated_at"], "lexical":json.dumps(lex, ensure_ascii=False)}]}
    u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{po['id']}/", headers=hdr(), json=body, timeout=30)
    print(f"  -> PUT {u.status_code}" + ("" if u.status_code==200 else f" :: {u.text[:300]}"))
print("\nDRY RUN. Re-run with --apply." if DRY else "\nDONE.")
