"""Phase 3 — Rewriting: generate article paragraphs + intro via Claude."""

import json
import logging
from pathlib import Path

import anthropic

from .utils import RateLimiter

logger = logging.getLogger(__name__)
_rl = RateLimiter(calls_per_second=1.0)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

ARTICLE_SYSTEM = """\
Eres un desarrollador español que escribe una newsletter técnica semanal. Tu tono es:
- Directo y sin bullshit corporativo
- Técnico pero accesible (asumes que el lector sabe programar)
- Opinionado — no tienes miedo de decir si algo es bueno o malo
- Casual pero profesional, como hablar con un colega dev
- NUNCA uses frases como "en el vertiginoso mundo de la IA" o "no te quedes atrás"
- NUNCA copies texto del artículo original, reescribe completamente con tu propia voz

Escribe un párrafo de 80-120 palabras en español sobre esta noticia para la newsletter.

El párrafo debe:
1. Empezar con un titular llamativo en negrita (max 10 palabras)
2. Explicar qué pasó y por qué importa
3. Incluir tu opinión o un ángulo práctico ("esto significa que ahora puedes...", \
"ojo con esto porque...")
4. Terminar con el link a la fuente en formato Markdown: [leer más](url)

Responde SOLO con el párrafo en formato Markdown."""

REPO_SYSTEM = """\
Eres un desarrollador español que escribe la sección "Repo de la semana" de una \
newsletter técnica sobre AI developer tools. Tu tono es entusiasta pero práctico.

Escribe 120-150 palabras en español sobre este repositorio de GitHub.

El texto debe:
1. Empezar con el nombre del repo en negrita
2. Explicar qué hace y para quién es útil
3. Mencionar las estrellas como señal de tracción en la comunidad
4. Dar un ángulo práctico: "puedes usarlo para...", "encaja bien si..."
5. Terminar con el link: [ver en GitHub](url)

Responde SOLO con el texto en formato Markdown."""

TOOL_SYSTEM = """\
Eres un desarrollador español que escribe la sección "Herramienta de la semana" de una \
newsletter técnica sobre AI developer tools. Eliges UNA herramienta que merece la pena probar \
esta semana y explicas por qué, con honestidad.

Escribe 100-140 palabras en español sobre esta herramienta.

El texto debe:
1. Empezar con el nombre de la herramienta en negrita
2. Explicar qué hace y qué problema resuelve
3. Dar un ángulo de "pruébala esta semana": para qué la usarías, en qué encaja
4. Ser honesto sobre sus límites o para quién NO es
5. Terminar con el link: [probarla](url)

Responde SOLO con el texto en formato Markdown."""

INTRO_SYSTEM = """\
Eres el editor de DevAI, una newsletter técnica semanal sobre AI developer tools en español.

Escribe un párrafo de introducción de 60-80 palabras para la edición de esta semana.

El párrafo debe:
- Ser conversacional y directo
- Mencionar brevemente 2-3 de los temas principales de esta edición
- NO empezar con "Hola" o "Buenos días" genérico — sé creativo con la apertura
- Terminar con una frase que invite a seguir leyendo

Responde SOLO con el párrafo, sin formato Markdown especial."""


# ---------------------------------------------------------------------------
# Claude call helpers
# ---------------------------------------------------------------------------

def _call(client: anthropic.Anthropic, model: str, max_tokens: int, system: str, user: str) -> str:
    _rl.wait()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def _rewrite_article(client: anthropic.Anthropic, model: str, max_tokens: int, item: dict) -> str:
    user = (
        f"Título: {item.get('original_title', '')}\n"
        f"Fuente: {item.get('source', '')}\n"
        f"Descripción: {item.get('snippet', '')}\n"
        f"URL: {item.get('original_url', '')}\n"
        f"Categoría: {item.get('category', '')}\n"
        f"Razón de relevancia: {item.get('relevance_reason', '')}"
    )
    return _call(client, model, max_tokens, ARTICLE_SYSTEM, user)


def _rewrite_repo(client: anthropic.Anthropic, model: str, max_tokens: int, item: dict) -> str:
    user = (
        f"Nombre: {item.get('original_title', '')}\n"
        f"URL: {item.get('original_url', '')}\n"
        f"Descripción: {item.get('snippet', '')}\n"
        f"Estrellas en GitHub: {item.get('stars', 'N/A')}\n"
        f"Lenguaje: {item.get('language', 'N/A')}\n"
        f"Razón de relevancia: {item.get('relevance_reason', '')}"
    )
    return _call(client, model, max_tokens + 100, REPO_SYSTEM, user)


def _rewrite_tool(client: anthropic.Anthropic, model: str, max_tokens: int, item: dict) -> str:
    user = (
        f"Herramienta: {item.get('original_title', '')}\n"
        f"Fuente: {item.get('source', '')}\n"
        f"Descripción: {item.get('snippet', '')}\n"
        f"URL: {item.get('original_url', '')}\n"
        f"Razón de relevancia: {item.get('relevance_reason', '')}"
    )
    return _call(client, model, max_tokens + 100, TOOL_SYSTEM, user)


def _generate_intro(
    client: anthropic.Anthropic, model: str, article_items: list[dict]
) -> str:
    summaries = [
        item.get("relevance_reason") or item.get("original_title", "")
        for item in article_items[:5]
    ]
    user = "Temas de esta edición:\n" + "\n".join(f"- {s}" for s in summaries)
    return _call(client, model, 200, INTRO_SYSTEM, user)


def _fallback_content(item: dict, is_repo: bool = False) -> str:
    """Minimal fallback if Claude call fails."""
    title = item.get("original_title", "Sin título")
    url = item.get("original_url", "#")
    snippet = item.get("snippet", "")
    link_text = "ver en GitHub" if is_repo else "leer más"
    return f"**{title}**\n\n{snippet}\n\n[{link_text}]({url})"


# ---------------------------------------------------------------------------
# Phase entry point
# ---------------------------------------------------------------------------

def run(config: dict, curated_file: Path, data_dir: Path, date_str: str) -> Path:
    output = data_dir / f"articles_{date_str}.json"

    if output.exists():
        logger.info(f"Rewriting: {output.name} already exists — skipping (idempotent)")
        return output

    curated: list[dict] = json.loads(curated_file.read_text(encoding="utf-8"))
    if not curated:
        logger.warning("Curated list is empty — creating minimal articles file")
        result = {"date": date_str, "intro": "Sin novedades esta semana.", "articles": [], "repo_of_week": None, "tool_of_week": None}
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    logger.info(f"Rewriting: {len(curated)} curated items")
    claude_cfg = config.get("claude", {})
    model = claude_cfg.get("model", "claude-sonnet-4-20250514")
    max_tokens = claude_cfg.get("max_tokens_rewrite", 500)
    client = anthropic.Anthropic()

    # Separate out the best GitHub repo for the "Repo de la semana" section.
    # Strategy: first item with type=github or category=repo (already ranked by Claude).
    repo_item: dict | None = None
    tool_item: dict | None = None
    regular_items: list[dict] = []

    for item in sorted(curated, key=lambda x: x.get("rank", 99)):
        is_repo = item.get("type") == "github" or item.get("category") == "repo"
        is_tool = item.get("category") == "tool"
        if is_repo and repo_item is None:
            repo_item = item
        elif is_tool and tool_item is None:
            tool_item = item
        else:
            regular_items.append(item)

    # Rewrite regular articles
    written_articles: list[dict] = []
    for item in regular_items:
        short_title = item.get("original_title", "")[:60]
        logger.info(f"  Rewriting [{item.get('rank')}] {short_title}…")
        try:
            content = _rewrite_article(client, model, max_tokens, item)
        except Exception as exc:
            logger.error(f"  Rewrite failed for rank {item.get('rank')}: {exc}")
            content = _fallback_content(item)
        written_articles.append({**item, "content": content})

    # Rewrite repo of the week
    written_repo: dict | None = None
    if repo_item:
        short_title = repo_item.get("original_title", "")[:60]
        logger.info(f"  Rewriting repo of the week: {short_title}…")
        try:
            content = _rewrite_repo(client, model, max_tokens, repo_item)
        except Exception as exc:
            logger.error(f"  Repo rewrite failed: {exc}")
            content = _fallback_content(repo_item, is_repo=True)
        written_repo = {**repo_item, "content": content}

    # Rewrite tool of the week
    written_tool: dict | None = None
    if tool_item:
        logger.info(f"  Rewriting tool of the week: {tool_item.get('original_title', '')[:60]}…")
        try:
            content = _rewrite_tool(client, model, max_tokens, tool_item)
        except Exception as exc:
            logger.error(f"  Tool rewrite failed: {exc}")
            content = _fallback_content(tool_item)
        written_tool = {**tool_item, "content": content}

    # Generate weekly intro
    logger.info("  Generating intro paragraph…")
    try:
        intro = _generate_intro(client, model, regular_items)
    except Exception as exc:
        logger.error(f"  Intro generation failed: {exc}")
        intro = (
            f"Otra semana cargada de novedades en el ecosistema de AI developer tools. "
            f"Esta edición: {len(written_articles)} historias que merece la pena leer."
        )

    result = {
        "date": date_str,
        "intro": intro,
        "articles": written_articles,
        "repo_of_week": written_repo,
        "tool_of_week": written_tool,
    }

    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        f"Rewriting complete: {len(written_articles)} articles "
        f"+ {'1 repo' if written_repo else 'no repo'} "
        f"+ {'1 tool' if written_tool else 'no tool'} -> {output}"
    )
    return output
