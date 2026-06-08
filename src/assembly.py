"""Phase 4 — Assembly: render HTML + plaintext newsletter via Jinja2 templates."""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils import markdown_to_html, markdown_to_plain

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

CATEGORY_COLORS: dict[str, str] = {
    "launch":   "#10b981",  # emerald
    "update":   "#3b82f6",  # blue
    "workflow": "#8b5cf6",  # violet
    "tool":     "#f59e0b",  # amber
    "repo":     "#06b6d4",  # cyan
    "industry": "#ef4444",  # red
}

CATEGORY_ES: dict[str, str] = {
    "launch":   "lanzamiento",
    "update":   "actualización",
    "workflow": "workflow",
    "tool":     "herramienta",
    "repo":     "repo",
    "industry": "industria",
}

FREQUENCY_ES: dict[str, str] = {
    "weekly":  "semana",
    "monthly": "mes",
    "daily":   "día",
}

MONTH_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Reply-loop engagement engine: every issue ends with a question that invites a reply
# (replies are the strongest deliverability + retention signal a small list has).
# Override per issue via the articles data `reply_question` or newsletter config.
DEFAULT_REPLY_QUESTION = "¿Qué herramienta de IA estás usando más esta semana?"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_date(date_str: str) -> str:
    """'2025-01-15' → '15 de enero de 2025'"""
    try:
        parts = date_str.split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{d} de {MONTH_ES[m - 1]} de {y}"
    except Exception:
        return date_str


def _build_article_ctx(item: dict) -> dict:
    cat = item.get("category", "tool").lower()
    content_md = item.get("content", "")
    return {
        **item,
        "badge_color": CATEGORY_COLORS.get(cat, "#6b7280"),
        "category_label": CATEGORY_ES.get(cat, cat),
        "content_html": markdown_to_html(content_md),
        "content_plain": markdown_to_plain(content_md),
    }


def _build_jinja_env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        # autoescape=False so we can inject pre-built HTML safely via | safe
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ---------------------------------------------------------------------------
# Phase entry point
# ---------------------------------------------------------------------------

def run(
    config: dict, articles_file: Path, output_dir: Path, date_str: str
) -> tuple[Path, Path]:
    html_out = output_dir / f"newsletter_{date_str}.html"
    txt_out = output_dir / f"newsletter_{date_str}.txt"

    if html_out.exists() and txt_out.exists():
        logger.info("Assembly: output files already exist — skipping (idempotent)")
        return html_out, txt_out

    data: dict = json.loads(articles_file.read_text(encoding="utf-8"))
    nl_cfg = config.get("newsletter", {})
    freq = nl_cfg.get("frequency", "weekly")

    articles_ctx = [_build_article_ctx(a) for a in data.get("articles", [])]
    repo_ctx = _build_article_ctx(data["repo_of_week"]) if data.get("repo_of_week") else None
    tool_ctx = _build_article_ctx(data["tool_of_week"]) if data.get("tool_of_week") else None

    ctx = {
        "newsletter": {
            **nl_cfg,
            "frequency_label": FREQUENCY_ES.get(freq, freq),
        },
        "date_str": date_str,
        "date_display": _format_date(date_str),
        "intro": data.get("intro", ""),
        "articles": articles_ctx,
        "repo_of_week": repo_ctx,
        "tool_of_week": tool_ctx,
        "reply_question": (
            data.get("reply_question") or nl_cfg.get("reply_question") or DEFAULT_REPLY_QUESTION
        ),
        "category_colors": CATEGORY_COLORS,
    }

    templates_dir = Path(__file__).parent.parent / "templates"
    env = _build_jinja_env(templates_dir)

    # Render HTML
    html_tmpl = env.get_template("newsletter.html.j2")
    html_out.write_text(html_tmpl.render(**ctx), encoding="utf-8")

    # Render plaintext
    txt_tmpl = env.get_template("newsletter.txt.j2")
    txt_out.write_text(txt_tmpl.render(**ctx), encoding="utf-8")

    logger.info(f"Assembly complete -> {html_out.name} + {txt_out.name}")
    return html_out, txt_out
