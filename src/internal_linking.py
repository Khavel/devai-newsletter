"""Auto-inject internal links from newsletters to evergreen guides."""

import re

INTERNAL_LINKS: dict[str, str] = {
    "Claude Code":    "/guias-claude-code/",
    "Cursor":         "/guias-cursor-ai/",
    "MCP":            "/guias-mcp-servers/",
    "GitHub Copilot": "/guias-github-copilot/",
    "vibe coding":    "/guias-vibe-coding/",
    "Vibe Coding":    "/guias-vibe-coding/",
}

# Patterns compiled once at module load
_COMPILED: list[tuple[re.Pattern, str, str]] = []
for _kw, _path in INTERNAL_LINKS.items():
    _pat = re.compile(
        r"(?<!</?a[^>]*>)(?<!\w)(" + re.escape(_kw) + r")(?!\w)(?![^<]*</a>)",
        re.IGNORECASE,
    )
    _COMPILED.append((_pat, _path, _kw))


def inject_internal_links(html: str, base_url: str = "https://devaisemanal.com") -> str:
    """Replace the first occurrence of each keyword with a link to its evergreen guide.

    Only replaces text that is NOT already inside an <a> tag. Operates case-insensitively
    but preserves the original casing in the displayed text.
    """
    for pattern, path, keyword in _COMPILED:
        url = f"{base_url}{path}"

        def _replace(m: re.Match, _url: str = url, _kw: str = keyword) -> str:
            return f'<a href="{_url}" title="Guía de {_kw}">{m.group(1)}</a>'

        html, count = pattern.subn(_replace, html, count=1)
        if count:
            continue  # Only first occurrence per keyword
    return html
