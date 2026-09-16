"""Constantes para el remate de segunda pagina + CTA de formacion (2026-09-16).

Retitulos de intencion para las 5 URL que Mangools situa entre la 10a y la 47a en
Espana (tabnine, bolt.new, playwright mcp, v0, mcp inspector) y el bloque CTA que
sustituye la llamada a suscribirse por una llamada a la linea de formacion en las
guias de Claude Code / .NET. Este modulo solo define datos: la logica que llama a
Ghost llega en un paso posterior (no ejecutar nada de aqui todavia).
"""
import sys, json, os, time, hashlib, hmac, base64, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
GHOST = "https://devaisemanal.com"

def _key_parts():
    return admin_api_key.split(":", 1)

def token():
    key_id, secret = _key_parts()
    now = int(time.time())
    def b(d): return base64.urlsafe_b64encode(d).decode().rstrip("=")
    h = b(json.dumps({"alg":"HS256","typ":"JWT","kid":key_id},separators=(",",":")).encode())
    p = b(json.dumps({"iat":now,"exp":now+300,"aud":"/admin/"},separators=(",",":")).encode())
    s = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b(s)}"

def hdr():
    return {"Authorization": f"Ghost {token()}", "Accept-Version": "v5.0", "Content-Type": "application/json"}

# (slug, meta_title <=60, meta_description 120-160) -- keyword al principio, intencion + ano.
# Slugs confirmados contra Ghost en vivo con `python _list_ghost_posts.py` el 2026-09-16
# (ver task-1-report.md): tabnine y playwright-mcp y mcp-inspector se corrigieron porque el
# slug que Mangools asocia a la URL no coincidia con el slug real en Ghost.
RETITLES = [
    ("tabnine-autocompletado-codigo-ia",  # corregido: el brief traia "tabnine-que-es-precios-alternativas" (no existe).
     # CONFIRMADO por el controlador con datos de Search Console (2026-09-16, ultimos 90 dias):
     # 220 impresiones y posicion media 9.4 para la query "tabnine", frente a 3 y 13
     # impresiones de los otros dos posts de Tabnine -- ya no es una inferencia de Task 1.
     "Tabnine: qué es, precios y alternativas (2026)",
     "Tabnine a fondo: autocompletado con IA que corre en local, qué modelos usa, cuánto cuesta por usuario y cuándo compensa frente a Copilot o Cursor en 2026."),
    ("bolt-new-crear-apps-ia-navegador",  # confirmado
     "Bolt.new: qué es, precios y límites reales (2026)",
     "Bolt.new genera y despliega apps completas desde el navegador. Qué hace bien, dónde se rompe, cuánto cuesta en tokens y cuándo elegir v0 o Lovable en su lugar."),
    ("playwright-mcp-agentes-ia-testing-ui",  # corregido: el brief traia "playwright-mcp-automatizar-navegador-agentes" (no existe)
     "Playwright MCP: automatiza el navegador desde tu agente",
     "Cómo instalar y usar Playwright MCP con Claude Code, Cursor o Copilot: configuración, permisos, casos de uso y errores típicos al automatizar el navegador."),
    ("v0-dev-generar-ui-ia",  # confirmado
     "v0 de Vercel: cómo funciona, precios y alternativas",
     "v0.dev genera componentes React/Next.js desde texto. Calidad del código, límites del plan gratuito, precios 2026 y mejores alternativas para generar UI con IA."),
    ("mcp-inspector-testing-servidores",  # corregido: el brief traia "mcp-inspector-depurar-servidores-mcp" (no existe)
     "MCP Inspector: depura tu servidor MCP paso a paso",
     "Guía de MCP Inspector: cómo lanzarlo, conectar un servidor local, probar tools y resources, leer errores y validar el esquema antes de publicar tu servidor MCP."),
]

FORMACION_URL = "https://devaisemanal.com/formacion/?utm_source=article&utm_medium=cta&utm_campaign=formacion"

CTA_FORMACION = (
    '<div id="cta-formacion" style="background:#f0f4ff;border-left:4px solid #4f46e5;'
    'padding:18px 20px;border-radius:8px;margin:28px 0">'
    '<p style="margin:0 0 6px;font-weight:600;font-size:1.05em">'
    "¿Quieres que tu equipo trabaje así con IA?</p>"
    '<p style="margin:0 0 14px;color:#444">'
    "Imparto talleres prácticos de IA aplicada para equipos .NET y sesiones 1:1 para desarrolladores. "
    "Lo que se enseña es lo que uso cada día en producción, no teoría de curso.</p>"
    f'<a href="{FORMACION_URL}" '
    'style="background:#4f46e5;color:#fff;padding:9px 22px;border-radius:6px;'
    'text-decoration:none;font-weight:600;display:inline-block">Ver la formación</a>'
    "</div>"
)

CTA_TARGET_SLUGS = [
    "claude-code-dotnet-csharp-guia",
    "tutoriales-claude-code-aceptar-automaticamente",
    "agents-md-claude-md-memoria-proyecto",
    "claude-code-que-es-guia-completa",
    # "guias-claude-code" quitado (dry-run 2026-09-16): NO EXISTE como POST -- es una
    # Ghost PAGE (/guias-claude-code/, "Claude Code: Guía Definitiva para Desarrolladores"),
    # confirmado via GET /ghost/api/admin/pages/slug/guias-claude-code/. insert_html_node
    # de _ghost_cta_surgery.py solo edita posts (API /admin/posts/), no pages; añadir esa
    # ruta esta fuera del alcance de esta tarea (Task 2 solo toca este fichero). No se aplica
    # a un slug adivinado.
    "claude-code-terminal-ia-guia",
    "codex-cli-configuracion-agents-md-permisos",
]

FORMACION_PAGE = {
    "slug": "formacion",
    "title": "Formación en IA aplicada para equipos de desarrollo .NET",
    "html": (
        "<p>Soy Alejandro Oceja, ingeniero de software senior (.NET y Azure) y autor de DevAI Semanal. "
        "Opero agentes de IA en producción a diario y enseño exactamente eso: cómo integrar Claude Code, "
        "Copilot, Cursor y MCP en el trabajo real de un equipo, sin humo.</p>"
        "<h2>Taller «IA para equipos .NET» (1 día, presencial u online)</h2>"
        "<ul>"
        "<li>Asistentes de código en el flujo real: de autocompletar a agentes que ejecutan tareas.</li>"
        "<li>Contexto que funciona: AGENTS.md, CLAUDE.md, memoria de proyecto y permisos.</li>"
        "<li>MCP: conectar herramientas propias (BD, CI, navegador) a los agentes con seguridad.</li>"
        "<li>Control de coste y de riesgo: modos automáticos, sandboxes y revisión.</li>"
        "</ul>"
        "<p>Formato: un día para un equipo de 4 a 12 personas, sobre vuestro propio código. "
        "Bonificable por FUNDAE a través de vuestra entidad organizadora o gestoría.</p>"
        "<h2>Sesiones 1:1</h2>"
        "<p>Para desarrolladores que quieren dar el salto con su propio proyecto: sesiones online prácticas, "
        "primera media hora de evaluación sin coste para decirte honestamente si puedo ayudarte.</p>"
        "<h2>Cómo empezar</h2>"
        "<p>Escríbeme a <a href=\"mailto:a.oceja.dev@gmail.com\">a.oceja.dev@gmail.com</a> o por "
        "<a href=\"https://www.linkedin.com/in/alejandrooceja\" rel=\"noopener\">LinkedIn</a> "
        "contándome qué hace tu equipo y qué te gustaría que hiciera con IA. Respondo en menos de dos días.</p>"
    ),
}

# Importar _ghost_cta_surgery.py por ruta (como hacen los tests) para reutilizar
# insert_html_node/get_post sin reejecutar la cabecera de token() a nivel de módulo.
_surgery_spec = importlib.util.spec_from_file_location(
    "_ghost_cta_surgery", Path(__file__).parent / "_ghost_cta_surgery.py")
surgery = importlib.util.module_from_spec(_surgery_spec)
_surgery_spec.loader.exec_module(surgery)

BACKUP_DIR = Path(__file__).parent / "output" / "backups"


def ensure_formacion_page():
    """Crea la página /formacion/ si no existe; si existe, no la toca (idempotente)."""
    r = httpx.get(f"{GHOST}/ghost/api/admin/pages/slug/{FORMACION_PAGE['slug']}/?fields=id,url", headers=hdr(), timeout=30)
    if r.status_code == 200:
        print(f"  SKIP página /{FORMACION_PAGE['slug']}/ ya existe: {r.json()['pages'][0]['url']}")
        return
    body = {"pages": [{
        "title": FORMACION_PAGE["title"],
        "slug": FORMACION_PAGE["slug"],
        "status": "published",
        "html": FORMACION_PAGE["html"],
        "meta_title": "Formación en IA para equipos .NET | DevAI Semanal",
        "meta_description": "Talleres de un día de IA aplicada para equipos .NET y sesiones 1:1 para desarrolladores, impartidos por el autor de DevAI Semanal. Bonificable por FUNDAE.",
    }]}
    if DRY:
        print(f"  [DRY RUN] crearía la página /{FORMACION_PAGE['slug']}/")
        return
    u = httpx.post(f"{GHOST}/ghost/api/admin/pages/?source=html", headers=hdr(), json=body, timeout=30)
    print(f"  -> POST página {u.status_code}" + ("" if u.status_code == 201 else f" :: {u.text[:300]}"))


def retitle_all():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for slug, mt, md in RETITLES:
        r = httpx.get(f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?fields=id,updated_at,meta_title,meta_description,title",
                      headers=hdr(), timeout=30)
        if r.status_code == 404:
            print(f"\n=== {slug} === NO EXISTE: confirma el slug con _list_ghost_posts.py")
            continue
        po = r.json()["posts"][0]
        (BACKUP_DIR / f"{slug}-{time.strftime('%Y%m%d')}.json").write_text(json.dumps(po, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n=== {slug} ===\n  OLD: {po.get('meta_title')}\n  NEW: {mt} ({len(mt)})\n  OLD desc: {po.get('meta_description')}\n  NEW desc: {md} ({len(md)})")
        if DRY:
            print("  [DRY RUN]"); continue
        u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{po['id']}/", headers=hdr(), timeout=30,
                      json={"posts": [{"updated_at": po["updated_at"], "meta_title": mt, "meta_description": md}]})
        print(f"  -> PUT {u.status_code}" + ("" if u.status_code == 200 else f" :: {u.text[:300]}"))


_orig_surgery_put_post = surgery.put_post


def _guarded_put_post(slug, old_len):
    """Envuelve surgery.put_post para abortar si el nuevo cuerpo (lexical) es MAS CORTO
    que el original -- _ghost_cta_surgery.py no trae ningun guard de este tipo, asi que
    se añade aqui en tiempo de ejecucion (monkeypatch), sin tocar ese fichero."""
    def guarded(post_id, body_posts):
        new_lex = body_posts.get("lexical")
        if new_lex is not None and old_len and len(new_lex) < old_len:
            print(f"  ABORT PUT {slug}: nuevo lexical ({len(new_lex)} chars) mas corto que "
                  f"el original ({old_len} chars) -- no se aplica, revisar a mano.")
            return False
        return _orig_surgery_put_post(post_id, body_posts)
    return guarded


def inject_formacion_cta():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    surgery.DRY = DRY
    for slug in CTA_TARGET_SLUGS:
        try:
            po = surgery.get_post(slug)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"\n=== {slug} === NO EXISTE: confirma el slug con _list_ghost_posts.py")
                continue
            raise
        (BACKUP_DIR / f"{slug}-{time.strftime('%Y%m%d')}.json").write_text(json.dumps(po, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n=== {slug} ===")
        old_len = len(po.get("lexical") or "")
        surgery.put_post = _guarded_put_post(slug, old_len)
        try:
            surgery.insert_html_node(slug, "cta-formacion", CTA_FORMACION, "mid")
        finally:
            surgery.put_post = _orig_surgery_put_post


DRY = "--apply" not in sys.argv


def main():
    print("== 0. página /formacion/ =="); ensure_formacion_page()
    print("\n== 1. retítulos de las 5 URL en segunda página =="); retitle_all()
    print("\n== 2. CTA de formación en las guías de Claude Code/.NET =="); inject_formacion_cta()


if __name__ == "__main__":
    main()
