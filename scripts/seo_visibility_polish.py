"""Apply final SEO visibility polish to Ghost.

Updates:
- Short meta titles for the newest articles.
- Featured images for posts that still lack them.
- Home metadata and cover image.
- Tag descriptions for /tag/guias/ and /tag/newsletter/.
- A stronger About page for trust and editorial transparency.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_evergreen_articles import (  # noqa: E402
    GHOST_URL,
    headers,
)


ROOT = Path(__file__).resolve().parents[1]


HOME_SETTINGS = {
    "meta_title": "DevAI Semanal - IA para desarrolladores en español",
    "meta_description": "Newsletter y guías en español sobre Claude Code, Cursor, GitHub Copilot, MCP, agentes de IA y herramientas para programadores.",
    "og_title": "DevAI Semanal - IA para desarrolladores",
    "og_description": "Cada semana: herramientas de IA para programadores, guías prácticas y novedades de Claude, Cursor, Copilot y MCP.",
    "twitter_title": "DevAI Semanal - IA para desarrolladores",
    "twitter_description": "Newsletter y guías sobre herramientas de IA para devs: Claude, Cursor, Copilot, MCP y agentes.",
    "cover_image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1600&h=900&fit=crop&q=80",
}


SHORT_META_TITLES = {
    "github-copilot-ai-credits-pago-por-uso": "GitHub Copilot AI Credits: coste y límites",
    "copilot-code-review-minutos-github-actions": "Copilot Code Review y GitHub Actions",
    "github-copilot-datos-entrenamiento-privacidad": "Copilot y privacidad: guía para equipos",
    "serena-mcp-busqueda-semantica-codigo": "Serena MCP: código semántico para agentes",
    "rtk-proxy-cli-reducir-tokens-ia": "RTK: menos tokens para agentes de IA",
    "zed-parallel-agents-editor-ia": "Zed Parallel Agents: guía práctica",
    "vs-code-copilot-coauthored-by-commits": "VS Code y Copilot Co-authored-by",
}


FEATURED_IMAGES = {
    "v0-dev-generar-ui-ia": "https://images.unsplash.com/photo-1559028012-481c04fa702d?w=1200&h=628&fit=crop&q=80",
    "bolt-new-crear-apps-ia-navegador": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1200&h=628&fit=crop&q=80",
    "replit-programar-navegador-ia": "https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=1200&h=628&fit=crop&q=80",
    "amazon-q-developer-ia-aws": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=628&fit=crop&q=80",
    "tabnine-autocompletado-codigo-ia": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&h=628&fit=crop&q=80",
    "windsurf-ide-editor-ia": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=628&fit=crop&q=80",
    "github-copilot-ai-credits-pago-por-uso": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
    "copilot-code-review-minutos-github-actions": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&h=628&fit=crop&q=80",
    "github-copilot-datos-entrenamiento-privacidad": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1200&h=628&fit=crop&q=80",
    "serena-mcp-busqueda-semantica-codigo": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "rtk-proxy-cli-reducir-tokens-ia": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "zed-parallel-agents-editor-ia": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=628&fit=crop&q=80",
    "vs-code-copilot-coauthored-by-commits": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=1200&h=628&fit=crop&q=80",
    "real-time-chunking-rag-streaming": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
    "ia-apuestas-deportivas-modelos-riesgos": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-03-29": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-03-31": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-04-07": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-04-14": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-04-21": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-04-28": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-05-05": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-05-12": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "newsletter-2026-05-19": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
    "generadores-interfaces-ia-herramientas-ui": "https://images.unsplash.com/photo-1559028012-481c04fa702d?w=1200&h=628&fit=crop&q=80",
    "amazon-codewhisperer-vs-q-developer-ia-aws": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=628&fit=crop&q=80",
    "claude-code-terminal-ia-guia": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=1200&h=628&fit=crop&q=80",
    "mejores-editores-codigo-ia-2026": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=628&fit=crop&q=80",
    "mcp-model-context-protocol-guia": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "agentes-ia-programar-guia": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=628&fit=crop&q=80",
}


TAG_UPDATES = {
    "guias": {
        "description": "Guías prácticas en español sobre herramientas de IA para desarrolladores: Claude Code, Cursor, GitHub Copilot, MCP, agentes y editores.",
        "meta_title": "Guías de IA para desarrolladores - DevAI Semanal",
        "meta_description": "Guías prácticas sobre herramientas de IA para programadores: Claude Code, Cursor, GitHub Copilot, MCP, agentes y editores.",
    },
    "newsletter": {
        "description": "Archivo de ediciones semanales de DevAI Semanal con novedades y análisis de herramientas de IA para desarrolladores.",
        "meta_title": "Newsletter de IA para desarrolladores - DevAI Semanal",
        "meta_description": "Archivo de newsletters semanales sobre Claude, Cursor, Copilot, MCP y herramientas de IA para desarrolladores.",
    },
}


ABOUT_HTML = """<div style="background:#f8fafc;border-left:4px solid #0ea5e9;border-radius:8px;padding:22px 24px;margin:30px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:13px;font-weight:800;color:#0369a1;text-transform:uppercase;letter-spacing:.06em;margin:0 0 8px;">Criterio editorial</p>
  <p style="font-size:16px;color:#334155;line-height:1.7;margin:0;">DevAI Semanal prioriza herramientas que cambian el trabajo real de programar: asistentes de código, agentes, editores, MCP, automatización, privacidad, coste y flujos de equipo. No cubrimos cada lanzamiento; filtramos lo que puede afectar decisiones técnicas.</p>
</div>"""


ABOUT_BODY_HTML = f"""<h2>Herramientas de IA para desarrolladores, en español</h2>
<p><strong>DevAI Semanal</strong> es una publicación en español sobre herramientas de inteligencia artificial para desarrolladores. El objetivo es simple: ayudarte a decidir qué merece probarse, qué conviene vigilar y qué cambios afectan de verdad al trabajo diario de programar.</p>
<p>Cubrimos asistentes de código, agentes, editores, MCP, automatización, privacidad, coste, revisión de código y flujos de equipo. El foco no está en repetir notas de prensa, sino en explicar qué significa cada cambio para alguien que escribe, revisa o mantiene software.</p>
<h2>Qué publicamos</h2>
<p>Publicamos dos tipos de contenido. Las newsletters semanales resumen novedades relevantes del ecosistema: Claude Code, Cursor, GitHub Copilot, editores con IA, MCP, agentes, automatización y herramientas emergentes.</p>
<p>Las guías evergreen convierten esos temas en análisis más estables, con contexto, límites, casos de uso y enlaces a documentación oficial. Cuando una noticia es puntual, queda como newsletter. Cuando tiene intención de búsqueda clara o valor a medio plazo, la convertimos en guía.</p>
{ABOUT_HTML}
<h2>Cómo elegimos los temas</h2>
<p>No seguimos una lista de notas de prensa. Priorizamos señales que pueden cambiar una decisión técnica: cambios de pricing, nuevas capacidades de agentes, riesgos de privacidad, integraciones con repositorios, herramientas open source útiles, automatización de revisión de código y flujos que afectan a equipos reales.</p>
<p>También miramos si una herramienta resuelve un problema concreto: reducir tokens, navegar mejor un codebase, revisar PRs, generar interfaces, automatizar tareas o coordinar varios agentes sin perder trazabilidad.</p>
<h2>Fuentes y revisión</h2>
<p>Siempre que es posible usamos documentación oficial, repositorios, changelogs, páginas de producto y comunicaciones públicas de los proveedores. La automatización ayuda a recopilar señales y preparar borradores, pero el criterio editorial está en filtrar, ordenar y explicar qué significa cada cambio para un desarrollador.</p>
<p>Si una herramienta cambia de pricing, política de datos o nombre, actualizamos las guías cuando el cambio afecta a la utilidad del artículo. En un mercado tan rápido como el de IA para desarrollo, preferimos artículos revisables antes que piezas cerradas que envejecen en silencio.</p>
<h2>Quién está detrás</h2>
<p>DevAI Semanal lo mantiene Alejandro Oceja. La publicación nace de una necesidad práctica: seguir el ritmo de herramientas de IA para programar sin depender de hilos sueltos, notas de marketing o contenido en inglés sin contexto para equipos hispanohablantes.</p>
<h2>Contacto y correcciones</h2>
<p>Si ves un dato desactualizado, una herramienta importante que falta o una explicación que debería matizarse, puedes responder a cualquier edición de la newsletter o contactar desde los canales enlazados en la web. Las correcciones útiles se incorporan a las guías para que el archivo mejore con el tiempo.</p>
<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:30px;margin:34px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:20px;font-weight:750;margin:0 0 8px;color:#0c4a6e;">Recibe DevAI Semanal cada martes</p>
  <p style="font-size:15px;color:#374151;margin:0 0 22px;line-height:1.6;">Herramientas de IA para desarrolladores, en español y con contexto práctico.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:650;padding:13px 30px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis</a>
</div>"""


def get_post(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/posts/",
        headers=headers(admin_api_key),
        params={"filter": f"slug:{slug}", "fields": "id,slug,title,feature_image,updated_at,meta_title", "limit": "1"},
    )
    resp.raise_for_status()
    posts = resp.json().get("posts", [])
    return posts[0] if posts else None


def update_settings(client: httpx.Client, admin_api_key: str) -> None:
    updated = 0
    for key, value in HOME_SETTINGS.items():
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/settings/",
            headers=headers(admin_api_key),
            json={"settings": [{"key": key, "value": value}]},
        )
        if resp.status_code in (200, 201):
            updated += 1
        else:
            print(f"skipped setting {key}: {resp.status_code} {resp.text[:120]}")
        time.sleep(1)
    print(f"updated settings: {updated}")


def update_posts(client: httpx.Client, admin_api_key: str) -> None:
    for slug in sorted(set(FEATURED_IMAGES) | set(SHORT_META_TITLES)):
        post = get_post(client, admin_api_key, slug)
        if not post:
            print(f"missing: {slug}")
            continue
        payload = {"updated_at": post["updated_at"]}
        if slug in FEATURED_IMAGES:
            payload["feature_image"] = FEATURED_IMAGES[slug]
        if slug in SHORT_META_TITLES:
            payload["meta_title"] = SHORT_META_TITLES[slug]
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
            headers=headers(admin_api_key),
            json={"posts": [payload]},
        )
        resp.raise_for_status()
        print(f"updated: {slug}")
        time.sleep(1)


def get_tag(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/tags/slug/{slug}/",
        headers=headers(admin_api_key),
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    tags = resp.json().get("tags", [])
    return tags[0] if tags else None


def update_tags(client: httpx.Client, admin_api_key: str) -> None:
    for slug, update in TAG_UPDATES.items():
        tag = get_tag(client, admin_api_key, slug)
        if not tag:
            print(f"missing tag: {slug}")
            continue
        payload = {
            "name": tag["name"],
            "slug": tag["slug"],
            **update,
        }
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/tags/{tag['id']}/",
            headers=headers(admin_api_key),
            json={"tags": [payload]},
        )
        resp.raise_for_status()
        print(f"updated tag: {slug}")


def get_page(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/pages/",
        headers=headers(admin_api_key),
        params={"filter": f"slug:{slug}", "fields": "id,updated_at", "limit": "1"},
    )
    resp.raise_for_status()
    pages = resp.json().get("pages", [])
    return pages[0] if pages else None


def update_about(client: httpx.Client, admin_api_key: str) -> None:
    mobiledoc = json.dumps(
        {
            "version": "0.3.1",
            "atoms": [],
            "cards": [["html", {"html": ABOUT_BODY_HTML}]],
            "markups": [],
            "sections": [[10, 0]],
        },
        ensure_ascii=False,
    )
    payload = {
        "title": "Sobre DevAI Semanal",
        "slug": "about",
        "status": "published",
        "visibility": "public",
        "custom_excerpt": "Qué es DevAI Semanal, cómo elegimos temas y cómo revisamos guías sobre herramientas de IA para desarrolladores.",
        "meta_title": "Sobre DevAI Semanal - IA para desarrolladores",
        "meta_description": "Conoce DevAI Semanal: newsletter y guías en español sobre herramientas de IA para desarrolladores, fuentes y criterio editorial.",
        "mobiledoc": mobiledoc,
    }
    page = get_page(client, admin_api_key, "about")
    if page:
        payload["updated_at"] = page["updated_at"]
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/pages/{page['id']}/",
            headers=headers(admin_api_key),
            json={"pages": [payload]},
        )
    else:
        resp = client.post(
            f"{GHOST_URL}/ghost/api/admin/pages/",
            headers=headers(admin_api_key),
            json={"pages": [payload]},
        )
    resp.raise_for_status()
    print("updated: about")


def main() -> None:
    load_dotenv(ROOT / ".env")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not admin_api_key:
        raise SystemExit("GHOST_ADMIN_API_KEY is required")
    with httpx.Client(timeout=30) as client:
        update_settings(client, admin_api_key)
        update_tags(client, admin_api_key)
        update_about(client, admin_api_key)
        update_posts(client, admin_api_key)


if __name__ == "__main__":
    main()
