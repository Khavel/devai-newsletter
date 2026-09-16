"""Ejecucion contra Ghost del remate de segunda pagina + CTA de formacion (2026-09-16).

Retitulos de intencion para 5 URL (tabnine, bolt.new, playwright mcp, v0, mcp inspector)
y sustitucion/insercion del bloque CTA de suscripcion por uno de formacion en las guias de
Claude Code / .NET, mas la creacion idempotente de la pagina /formacion/. Dry-run por
defecto (sin --apply); "python _ghost_seo_actions_2026_09_16.py --apply" ejecuta de verdad
contra devaisemanal.com.

Backups: antes de cada PUT real se vuelca el post original a BACKUP_DIR con timestamp
unico (nunca se sobreescribe). BACKUP_DIR se puede fijar con la variable de entorno
DEVAI_BACKUP_DIR para que sobreviva a un `git worktree remove` de este checkout -- en la
ejecucion real (--apply) usar:
    DEVAI_BACKUP_DIR=C:\\Users\\ceja_\\Desktop\\Desarrollos\\devai-newsletter\\output\\backups\\2026-09-16-seo-actions
(el checkout principal, fuera de este worktree). Sin esa variable, cae a
<este_fichero>/output/backups/ (dentro del worktree -- solo vale para dry-runs/pruebas).
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

# Marcadores del CTA de suscripcion que este CTA de formacion sustituye (ver
# _ghost_cta_surgery.py: CTA_MID lleva id="cta-mid-article"; data-devai-signup-cta cubre
# cualquier otra variante histórica del mismo CTA que pudiera llevar ese atributo en vez
# del id).
_SIGNUP_CTA_MARKERS = ('id="cta-mid-article"', "data-devai-signup-cta")

CTA_TARGET_SLUGS = [
    "claude-code-dotnet-csharp-guia",
    # "tutoriales-claude-code-aceptar-automaticamente" se SALTA en replace_or_insert_cta
    # (ruling del controlador, 2026-09-16): este post no tiene cuerpo lexical, y el unico
    # camino para editarlo sin lexical es el fallback ?source=html, que (a) no pasa por el
    # guard anti-encogimiento, (b) deja un backup sin el cuerpo real (lexical null) y (c)
    # viola la regla del repo de que ?source=html solo vale para CREAR paginas, nunca para
    # editar un cuerpo existente. Se deja en la lista para que quede constancia de que
    # sigue pendiente (migrar el post a lexical en Ghost), pero se salta explicitamente.
    "tutoriales-claude-code-aceptar-automaticamente",
    "agents-md-claude-md-memoria-proyecto",
    "claude-code-que-es-guia-completa",
    # "guias-claude-code" quitado (dry-run 2026-09-16): NO EXISTE como POST -- es una
    # Ghost PAGE (/guias-claude-code/, "Claude Code: Guía Definitiva para Desarrolladores"),
    # confirmado via GET /ghost/api/admin/pages/slug/guias-claude-code/. Solo sabemos editar
    # posts (API /admin/posts/), no pages; añadir esa ruta esta fuera del alcance de esta
    # tarea. No se aplica a un slug adivinado.
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

DRY = "--apply" not in sys.argv

BACKUP_DIR = Path(os.getenv("DEVAI_BACKUP_DIR") or (Path(__file__).parent / "output" / "backups"))

# _ghost_cta_surgery.py hace `key_id, secret = admin_api_key.split(":", 1)` a nivel de
# modulo (el mismo bug que Task 1 arreglo aqui con _key_parts()) -- importarlo en el
# import de ESTE modulo reventaria sin .env y rompería la coleccion de
# tests/test_formacion_cta.py. Se importa por ruta perezosamente, solo cuando de verdad
# hace falta llamar a Ghost.
_surgery_mod = None


def _surgery():
    global _surgery_mod
    if _surgery_mod is None:
        spec = importlib.util.spec_from_file_location(
            "_ghost_cta_surgery", Path(__file__).parent / "_ghost_cta_surgery.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _surgery_mod = mod
    return _surgery_mod


def _backup_path(slug):
    return BACKUP_DIR / f"{slug}-{time.strftime('%Y%m%d-%H%M%S')}.json"


def _write_backup(slug, po):
    """Vuelca <po> a BACKUP_DIR con nombre unico (slug + fecha-hora); nunca sobreescribe."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = _backup_path(slug)
    if path.exists():
        raise FileExistsError(f"backup ya existe, no se sobreescribe: {path}")
    path.write_text(json.dumps(po, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _assert_not_shrinking(old_body, new_body, slug):
    """Guard anti-encogimiento: nunca aplicar un cuerpo mas corto que el original."""
    old_len, new_len = len(old_body or ""), len(new_body or "")
    if new_len < old_len:
        raise ValueError(
            f"{slug}: nuevo cuerpo ({new_len} chars) mas corto que el original ({old_len} chars) -- abortado")


def ensure_formacion_page():
    """Crea la página /formacion/ si no existe; si existe, no la toca (idempotente).
    Devuelve (ok, skipped, failed)."""
    try:
        r = httpx.get(f"{GHOST}/ghost/api/admin/pages/slug/{FORMACION_PAGE['slug']}/?fields=id,url", headers=hdr(), timeout=30)
        if r.status_code == 200:
            print(f"  SKIP página /{FORMACION_PAGE['slug']}/ ya existe: {r.json()['pages'][0]['url']}")
            return (0, 1, 0)
        if r.status_code != 404:
            print(f"  ERROR pagina /{FORMACION_PAGE['slug']}/: GET {r.status_code} {r.text[:200]}")
            return (0, 0, 1)
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
            return (1, 0, 0)
        u = httpx.post(f"{GHOST}/ghost/api/admin/pages/?source=html", headers=hdr(), json=body, timeout=30)
        print(f"  -> POST página {u.status_code}" + ("" if u.status_code == 201 else f" :: {u.text[:300]}"))
        return (1, 0, 0) if u.status_code == 201 else (0, 0, 1)
    except Exception as e:
        print(f"  ERROR pagina /{FORMACION_PAGE['slug']}/: {e}")
        return (0, 0, 1)


def retitle_all():
    """Devuelve (ok, skipped, failed)."""
    ok = skipped = failed = 0
    for slug, mt, md in RETITLES:
        try:
            r = httpx.get(f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?fields=id,updated_at,meta_title,meta_description,title",
                          headers=hdr(), timeout=30)
            if r.status_code == 404:
                print(f"\n=== {slug} === NO EXISTE: confirma el slug con _list_ghost_posts.py")
                skipped += 1
                continue
            if r.status_code != 200:
                print(f"\n=== {slug} === ERROR: GET {r.status_code} {r.text[:200]}")
                failed += 1
                continue
            po = r.json()["posts"][0]
            print(f"\n=== {slug} ===\n  OLD: {po.get('meta_title')}\n  NEW: {mt} ({len(mt)})\n  OLD desc: {po.get('meta_description')}\n  NEW desc: {md} ({len(md)})")
            if DRY:
                print(f"  [DRY RUN] would back up to {_backup_path(slug)}")
                print("  [DRY RUN]")
                ok += 1
                continue
            _write_backup(slug, po)
            u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{po['id']}/", headers=hdr(), timeout=30,
                          json={"posts": [{"updated_at": po["updated_at"], "meta_title": mt, "meta_description": md}]})
            print(f"  -> PUT {u.status_code}" + ("" if u.status_code == 200 else f" :: {u.text[:300]}"))
            if u.status_code == 200:
                ok += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n=== {slug} === ERROR: {e}")
            failed += 1
    print(f"\n[retitle_all] ok={ok} skipped={skipped} failed={failed}")
    return ok, skipped, failed


def _find_signup_cta_node(kids):
    """Busca en <kids> (children del root lexical) el PRIMER nodo html cuyo html
    contenga alguno de _SIGNUP_CTA_MARKERS y que este en la mitad del documento o antes.
    Devuelve su indice, o None si no hay ninguno que cumpla ambas condiciones."""
    mid = len(kids) / 2
    for i, c in enumerate(kids):
        if c.get("type") != "html":
            continue
        html = c.get("html") or ""
        if any(marker in html for marker in _SIGNUP_CTA_MARKERS) and i <= mid:
            return i
    return None


def replace_or_insert_cta(slug):
    """Para <slug>: si ya tiene cta-formacion, SKIP. Si no tiene lexical, SKIP (ver
    comentario en CTA_TARGET_SLUGS). Si hay un CTA de suscripcion en la mitad del cuerpo o
    antes, lo REEMPLAZA por CTA_FORMACION (mismo numero de nodos: sustituye la llamada a
    suscribirse por la de formacion, en vez de apilar las dos). Si no hay ninguno, cae al
    INSERT en el 'mid' original (misma heuristica que _ghost_cta_surgery.insert_html_node).
    Devuelve "ok" | "skipped"; lanza excepcion si algo va mal (el shrink guard incluido) --
    el caller (inject_formacion_cta) la captura y cuenta como failed."""
    s = _surgery()
    po = s.get_post(slug)
    print(f"\n=== {slug} ===")
    if not po.get("lexical"):
        print(f"  SKIP {slug}: sin cuerpo lexical (el fallback ?source=html esta "
              f"prohibido para editar; pendiente de migrar el post a lexical)")
        return "skipped"
    old_lexical = po["lexical"]
    if "cta-formacion" in old_lexical:
        print(f"  SKIP {slug}: cta-formacion ya presente")
        return "skipped"
    lex = json.loads(old_lexical)
    kids = lex["root"]["children"]
    idx = _find_signup_cta_node(kids)
    node = {"type": "html", "html": CTA_FORMACION, "version": 1}
    if idx is not None:
        marker = next(m for m in _SIGNUP_CTA_MARKERS if m in (kids[idx].get("html") or ""))
        print(f"  REPLACE {slug}: node {idx} ({marker})")
        kids[idx] = node
    else:
        heads = [i for i, c in enumerate(kids) if c.get("type") == "heading"]
        pos = heads[1] if len(heads) >= 2 else (heads[0] if heads else max(1, len(kids) // 3))
        print(f"  INSERT {slug}: at index {pos}/{len(kids)}")
        kids.insert(pos, node)
    new_lexical = json.dumps(lex, ensure_ascii=False)
    _assert_not_shrinking(old_lexical, new_lexical, slug)
    if DRY:
        print(f"  [DRY RUN] would back up to {_backup_path(slug)}")
        print("  [DRY RUN]")
        return "ok"
    _write_backup(slug, po)
    ok = s.put_post(po["id"], {"updated_at": po["updated_at"], "lexical": new_lexical})
    if not ok:
        raise RuntimeError(f"{slug}: PUT fallo (ver salida anterior)")
    return "ok"


def inject_formacion_cta():
    """Devuelve (ok, skipped, failed)."""
    ok = skipped = failed = 0
    for slug in CTA_TARGET_SLUGS:
        try:
            result = replace_or_insert_cta(slug)
            if result == "ok":
                ok += 1
            else:
                skipped += 1
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"\n=== {slug} === NO EXISTE: confirma el slug con _list_ghost_posts.py")
                skipped += 1
            else:
                print(f"\n=== {slug} === ERROR: {e}")
                failed += 1
        except Exception as e:
            print(f"\n=== {slug} === ERROR: {e}")
            failed += 1
    print(f"\n[inject_formacion_cta] ok={ok} skipped={skipped} failed={failed}")
    return ok, skipped, failed


def main():
    print(f"BACKUP_DIR = {BACKUP_DIR}")
    print("== 0. página /formacion/ =="); page = ensure_formacion_page()
    print("\n== 1. retítulos de las 5 URL en segunda página =="); retitles = retitle_all()
    print("\n== 2. CTA de formación en las guías de Claude Code/.NET =="); ctas = inject_formacion_cta()

    names = ("pagina", "retitulos", "cta")
    print("\n== TALLY ==")
    for name, (ok, skipped, failed) in zip(names, (page, retitles, ctas)):
        print(f"  {name}: ok={ok} skipped={skipped} failed={failed}")
    total_failed = page[2] + retitles[2] + ctas[2]
    if total_failed:
        print(f"\n{total_failed} fallo(s) -- revisar arriba.")
        sys.exit(1)


if __name__ == "__main__":
    main()
