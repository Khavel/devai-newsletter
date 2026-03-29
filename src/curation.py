"""Phase 2 — Curation: send raw items to Claude and get the 6-8 best ones."""

import json
import logging
import re
from pathlib import Path

import anthropic

from .utils import RateLimiter

logger = logging.getLogger(__name__)
_rl = RateLimiter(calls_per_second=1.0)

# ---------------------------------------------------------------------------
# System prompt (verbatim from spec)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Eres el editor de una newsletter técnica sobre AI developer tools en español. \
Tu audiencia son desarrolladores que usan herramientas como Claude Code, Cursor, \
Copilot, Cline, y MCP servers en su día a día.

De los siguientes items de noticias de la semana, selecciona los 6-8 más relevantes \
para esta audiencia. Prioriza:
1. Lanzamientos y updates de herramientas de coding con IA (nuevas versiones, features, pricing)
2. Comparativas y benchmarks entre herramientas
3. Nuevos MCP servers, plugins, o integraciones útiles
4. Técnicas y workflows de agentic coding que devs pueden aplicar hoy
5. Repos de GitHub trending que sean herramientas prácticas
6. Drama/movimientos de la industria que afecten al stack de un dev \
(adquisiciones, cambios de pricing, etc.)

Descarta: noticias de IA genérica sin impacto directo en devs, papers académicos \
sin aplicación práctica, rumores sin confirmar.

Responde SOLO con un JSON array. Cada item:
{
  "rank": 1,
  "original_title": "título original",
  "original_url": "url",
  "source": "fuente",
  "category": "launch|update|workflow|tool|repo|industry",
  "relevance_reason": "por qué importa a un dev en 1 frase"
}"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> list[dict]:
    """Strip possible markdown code fences and parse JSON array."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    text = re.sub(r"^```[a-z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    # If Claude accidentally added extra text before the array, find it
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _compact_item(item: dict) -> dict:
    """Return only the fields Claude needs to make curation decisions."""
    return {
        "title": item.get("title", "")[:200],
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "snippet": item.get("snippet", "")[:200],
        "type": item.get("type", ""),
        "stars": item.get("stars"),  # None for non-GitHub items
    }


# ---------------------------------------------------------------------------
# Phase entry point
# ---------------------------------------------------------------------------

def run(config: dict, raw_file: Path, data_dir: Path, date_str: str) -> Path:
    output = data_dir / f"curated_{date_str}.json"

    if output.exists():
        logger.info(f"Curation: {output.name} already exists — skipping (idempotent)")
        return output

    raw_items: list[dict] = json.loads(raw_file.read_text(encoding="utf-8"))
    logger.info(f"Curation: sending {len(raw_items)} items to Claude for selection")

    if not raw_items:
        logger.warning("No raw items to curate — creating empty curated file")
        output.write_text("[]", encoding="utf-8")
        return output

    compact = [_compact_item(it) for it in raw_items]
    claude_cfg = config.get("claude", {})
    client = anthropic.Anthropic()

    _rl.wait()
    message = client.messages.create(
        model=claude_cfg.get("model", "claude-sonnet-4-20250514"),
        max_tokens=claude_cfg.get("max_tokens_curation", 2000),
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Aquí están los {len(compact)} items recopilados esta semana:\n\n"
                    + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
                    + "\n\nSelecciona los 6-8 más relevantes para la newsletter."
                ),
            }
        ],
    )

    curated = _extract_json(message.content[0].text)

    # Enrich each curated item with snippet + type from the original raw data
    url_map: dict[str, dict] = {it["url"]: it for it in raw_items}
    for item in curated:
        orig = url_map.get(item.get("original_url", ""), {})
        item["snippet"] = orig.get("snippet", "")
        item["type"] = orig.get("type", "rss")
        item["stars"] = orig.get("stars", 0)
        item["language"] = orig.get("language", "")
        item["description"] = orig.get("description", "")

    output.write_text(
        json.dumps(curated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"Curation complete: {len(curated)} items selected → {output}")
    return output
