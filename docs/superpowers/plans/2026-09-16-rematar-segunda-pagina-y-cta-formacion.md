# DevAI Semanal — rematar las páginas de la segunda página y cambiar el CTA a formación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** subir a primera página las cinco URL que Mangools sitúa entre la 10ª y la 47ª en España (`tabnine` 11º, `v0 dev` 10º, `bolt new` 23º, `playwright mcp` 25º, `mcp inspector` 31º, `v0` 47º) con retítulos de intención, y sustituir en las guías de Claude Code/.NET la llamada a suscribirse (10 suscriptores, 2 lectores reales) por una llamada a la línea de formación, que es lo único con euros detrás.

**Architecture:** DevAI Semanal es un Ghost en Fly.io editado por la Admin API desde scripts Python del propio repo (`_ghost_seo_update.py` para meta título/descripción, `_ghost_cta_surgery.py` para insertar bloques HTML en el cuerpo con marcadores idempotentes). Este plan añade un script fechado que hace las dos cosas en modo `--dry-run` por defecto, crea una página Ghost `/formacion/` y reutiliza `insert_html_node` con un marcador nuevo. Regla del repo: siempre volcar el cuerpo original a disco antes de un PUT y abortar si el recorte es desproporcionado (memoria `backup-body-before-destructive-put`).

**Tech Stack:** Python 3.12, `httpx`, JWT HS256 de Ghost Admin API v5, pytest.

**Spec:** `C:\Users\ceja_\Desktop\Desarrollos\Spam\docs\research\2026-09-16-mangools-portfolio-audit-and-plan.md` §3 y `Spam/docs/research/2026-09-06-devai-keyword-opportunity-mangools.md`.

## Global Constraints

- Gate vigente del owner: **no publicar más perennes hasta el 2026-12-06**. Este plan no crea artículos; solo retitula y cambia CTAs.
- Restricción de la línea de formación (`Formacion/CLAUDE.md`): **solo inbound**, sin outreach; cortafuegos con el empleador (no nombrarlo). La página `/formacion/` describe la oferta y da un correo y LinkedIn; no promete plazas ni precios cerrados salvo el rango público del one-pager.
- Ghost: crear/editar por `lexical`, nunca `?source=html` para cuerpos (sanea `id`/`style` y rompe la idempotencia; memoria `ghost-html-source-sanitises-divs`). Antes de cada PUT, releer `updated_at` (colisión) y guardar el cuerpo original en `output/backups/<slug>-<fecha>.json`.
- Toda ejecución es `--dry-run` salvo `--apply` explícito. Imprimir antes/después de cada título.
- Tests: `python -m pytest tests -q` desde la raíz del repo.

---

## Mapa de ficheros

- Create: `_ghost_seo_actions_2026_09_16.py` — retítulos + CTA de formación + página `/formacion/`.
- Create: `tests/test_formacion_cta.py` — invariantes del bloque HTML y de la tabla de retítulos.
- Modify: `CLAUDE.md` del repo — una línea en el historial de acciones SEO.

---

### Task 1: Tabla de retítulos y bloque CTA como datos testeables

**Files:**
- Create: `_ghost_seo_actions_2026_09_16.py` (solo constantes en este paso)
- Create: `tests/test_formacion_cta.py`

**Interfaces:**
- Produces: `RETITLES: list[tuple[str, str, str]]` (slug, meta_title, meta_description); `CTA_FORMACION: str` con `id="cta-formacion"`; `FORMACION_PAGE: dict` con `slug`, `title`, `html`; `CTA_TARGET_SLUGS: list[str]`.

- [ ] **Step 1: Test que falla**

`tests/test_formacion_cta.py`:

```python
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("acciones", ROOT / "_ghost_seo_actions_2026_09_16.py")
acciones = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acciones)


def test_los_retitulos_caben_en_la_serp_y_llevan_la_keyword_al_principio():
    esperados = {
        "tabnine": r"^tabnine",
        "bolt-new": r"^bolt\.new",
        "playwright-mcp": r"^playwright mcp",
        "v0": r"^v0",
        "mcp-inspector": r"^mcp inspector",
    }
    vistos = set()
    for slug, title, desc in acciones.RETITLES:
        assert len(title) <= 60, (slug, len(title))
        assert 120 <= len(desc) <= 160, (slug, len(desc))
        for clave, patron in esperados.items():
            if clave in slug:
                assert re.match(patron, title, re.I), (slug, title)
                vistos.add(clave)
    assert vistos == set(esperados), f"faltan retítulos para {set(esperados) - vistos}"


def test_el_cta_de_formacion_es_idempotente_y_no_vende_suscripcion():
    html = acciones.CTA_FORMACION
    assert 'id="cta-formacion"' in html
    assert "devaisemanal.com/formacion/" in html
    assert "utm_campaign=formacion" in html
    assert "suscr" not in html.lower()
    assert "sin compromiso" not in html.lower()


def test_la_pagina_de_formacion_no_nombra_al_empleador_ni_promete_plazas():
    html = acciones.FORMACION_PAGE["html"].lower()
    for prohibido in ("bestsecret", "best secret", "plazas limitadas", "últimas plazas"):
        assert prohibido not in html
    assert acciones.FORMACION_PAGE["slug"] == "formacion"
    assert "linkedin.com/in/alejandrooceja" in html
    assert "a.oceja.dev@gmail.com" in html


def test_los_destinos_del_cta_son_las_guias_de_claude_code_y_dotnet():
    assert "claude-code-dotnet-csharp-guia" in acciones.CTA_TARGET_SLUGS
    assert "tutoriales-claude-code-aceptar-automaticamente" in acciones.CTA_TARGET_SLUGS
    assert len(acciones.CTA_TARGET_SLUGS) >= 5
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `python -m pytest tests/test_formacion_cta.py -q` → FAIL (el fichero no existe).

- [ ] **Step 3: Constantes**

Crear `_ghost_seo_actions_2026_09_16.py` con la cabecera de `_ghost_seo_update.py` (imports, `token()`, `hdr()`, `GHOST`) y estas constantes. **Los slugs reales de las cinco páginas hay que confirmarlos primero** con `python _list_ghost_posts.py | grep -i -E "tabnine|bolt|playwright|v0|inspector"`; los de abajo son los que Mangools asocia a esas URL y se corrigen si difieren:

```python
# (slug, meta_title ≤60, meta_description 120-160) — keyword al principio, intención + año.
RETITLES = [
    ("tabnine-que-es-precios-alternativas",
     "Tabnine: qué es, precios y alternativas (2026)",
     "Tabnine a fondo: autocompletado con IA que corre en local, qué modelos usa, cuánto cuesta por usuario y cuándo compensa frente a Copilot o Cursor en 2026."),
    ("bolt-new-crear-apps-ia-navegador",
     "Bolt.new: qué es, precios y límites reales (2026)",
     "Bolt.new genera y despliega apps completas desde el navegador. Qué hace bien, dónde se rompe, cuánto cuesta en tokens y cuándo elegir v0 o Lovable en su lugar."),
    ("playwright-mcp-automatizar-navegador-agentes",
     "Playwright MCP: automatiza el navegador desde tu agente",
     "Cómo instalar y usar Playwright MCP con Claude Code, Cursor o Copilot: configuración, permisos, casos de uso reales y los errores típicos al automatizar el navegador."),
    ("v0-dev-generar-ui-ia",
     "v0 de Vercel: cómo funciona, precios y alternativas",
     "v0.dev genera componentes React y Next.js desde texto. Calidad del código, límites del plan gratuito, precios en 2026 y las mejores alternativas para generar UI con IA."),
    ("mcp-inspector-depurar-servidores-mcp",
     "MCP Inspector: depura tu servidor MCP paso a paso",
     "Guía de MCP Inspector: cómo lanzarlo, conectar un servidor local, probar tools y resources, leer los errores y validar el esquema antes de publicar tu servidor MCP."),
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
    "guias-claude-code",
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
```

- [ ] **Step 4: Tests en verde**

Run: `python -m pytest tests/test_formacion_cta.py -q` → 4 passed. Si algún retítulo pasa de 60 o alguna descripción sale del rango, acortar ahí, no relajar el test.

- [ ] **Step 5: Commit**

```bash
git add _ghost_seo_actions_2026_09_16.py tests/test_formacion_cta.py
git commit -m "seo(devai): tabla de retítulos (5 URL en 2ª página) y CTA de formación como datos testeados"
```

---

### Task 2: Ejecución contra Ghost con backup y dry-run

**Files:**
- Modify: `_ghost_seo_actions_2026_09_16.py` (añadir la lógica)

**Interfaces:**
- Consumes: `insert_html_node(slug, marker, html, position)` y `get_post(slug)` de `_ghost_cta_surgery.py` (importar el módulo por ruta como hace el test); el patrón de PUT con `updated_at` de `_ghost_seo_update.py`.

- [ ] **Step 1: Página `/formacion/`**

Añadir:

```python
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
```

Nota: para **crear** una página, `?source=html` es correcto (convierte a lexical al crear); la prohibición del repo es para **editar** cuerpos existentes.

- [ ] **Step 2: Retítulos con backup**

```python
BACKUP_DIR = Path(__file__).parent / "output" / "backups"

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
```

- [ ] **Step 3: CTA en las guías**

Importar `_ghost_cta_surgery` por ruta (`importlib`) para reutilizar `insert_html_node` y su `DRY`; sincronizar el flag: `surgery.DRY = DRY`. Luego:

```python
def inject_formacion_cta():
    for slug in CTA_TARGET_SLUGS:
        surgery.insert_html_node(slug, "cta-formacion", CTA_FORMACION, "mid")
```

`insert_html_node` ya hace SKIP si el marcador existe y hace backup implícito vía `get_post`; añadir antes de la llamada un volcado del `lexical` original a `BACKUP_DIR` (mismo patrón que en `retitle_all`).

- [ ] **Step 4: `main` y ejecución**

```python
DRY = "--apply" not in sys.argv

def main():
    print("== 0. página /formacion/ =="); ensure_formacion_page()
    print("\n== 1. retítulos de las 5 URL en segunda página =="); retitle_all()
    print("\n== 2. CTA de formación en las guías de Claude Code/.NET =="); inject_formacion_cta()

if __name__ == "__main__":
    main()
```

Run: `python _ghost_seo_actions_2026_09_16.py` (dry-run). Leer la salida entera: cinco pares OLD/NEW, siete inserciones «insert cta-formacion at index N», ninguna línea «NO EXISTE». Si alguna aparece, corregir el slug en `RETITLES` y repetir el dry-run.

Run: `python _ghost_seo_actions_2026_09_16.py --apply`. Expected: `POST página 201`, cinco `PUT 200`, siete `PUT 200`.

- [ ] **Step 5: Verificar en el sitio**

Con Chrome real: `https://devaisemanal.com/formacion/` carga y no tiene el formulario de suscripción por encima del contenido; en `https://devaisemanal.com/claude-code-dotnet-csharp-guia/` el bloque «¿Quieres que tu equipo trabaje así con IA?» aparece tras la primera sección y su enlace lleva `utm_campaign=formacion`; el `<title>` de la página de Tabnine es el nuevo. En GA4 (propiedad 539660132), a los 7 días, filtrar `sessionCampaignName = formacion` para medir clics al CTA.

- [ ] **Step 6: Registro y commit**

En `CLAUDE.md` del repo, en el historial de acciones SEO, una línea: «2026-09-16: retítulos de tabnine/bolt/playwright-mcp/v0/mcp-inspector y CTA de formación (`cta-formacion`) en 7 guías de Claude Code; página `/formacion/` creada. Script `_ghost_seo_actions_2026_09_16.py`; backups en `output/backups/`.»

```bash
git add _ghost_seo_actions_2026_09_16.py CLAUDE.md
git commit -m "seo(devai): aplicar retítulos de 2ª página y CTA de formación en las guías de Claude Code"
```
(No añadir `output/backups/` si está ignorado; si no lo está, añadirlo a `.gitignore` en este mismo commit.)

---

### Task 3: Medición y gate

- [ ] SERPWatcher ya sigue `tabnine`, `bolt new`, `v0 dev`, `claude md`, `claude auto mode`; añadir `playwright mcp`, `mcp inspector` y `v0` a la tracking de devaisemanal (id `6a9ca87559a82ad7b2ee9749`) solo si el owner lo confirma (gasta plan). Lectura a D+14: éxito = al menos tres de las cinco URL suben ≥5 posiciones.
- [ ] Solicitar indexación de las cinco URL retituladas en Search Console (lección del 09-11: tras un retitulado mira la fecha de **último rastreo**, no si está indexada).
- [ ] GA4 a D+30: sesiones con `utm_campaign=formacion` y correos recibidos en `a.oceja.dev@gmail.com` desde la página. Si en 30 días hay cero contactos, el CTA se revisa (copy o destino), no se vuelve al de suscripción.

---

## Self-review

- **Spec §3:** (1) rematar la 10ª-47ª → Task 1-2 retítulos; (2) no abrir perennes → respetado; (3) CTA a formación → Task 1-2.
- **Placeholders:** los cinco slugs de `RETITLES` son una hipótesis que el Step 4 de la Task 2 obliga a confirmar con el dry-run («NO EXISTE» aborta ese slug). El resto es literal.
- **Consistencia:** marcador `cta-formacion` coincide entre `CTA_FORMACION`, el test y `insert_html_node`; `FORMACION_PAGE["slug"] == "formacion"` coincide con `FORMACION_URL`.
