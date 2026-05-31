"""Generate new SEO articles via Claude and publish directly to Ghost."""

import base64, hashlib, hmac, json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)
import anthropic
import httpx

GHOST_URL = "https://devaisemanal.com"

CTA_HTML = """<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:32px;margin:40px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:20px;font-weight:700;margin:0 0 8px;color:#0c4a6e;">Recibe una lectura semanal de herramientas IA para devs</p>
  <p style="font-size:15px;color:#374151;margin:0 0 24px;line-height:1.6;">Cada martes: Claude Code, Cursor, Copilot, MCP, agentes y herramientas nuevas. En español y sin ruido.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis</a>
</div>"""


# --- Ghost helpers ---

def _b64url(d: bytes) -> str:
    return base64.urlsafe_b64encode(d).decode().rstrip("=")

def ghost_jwt(admin_api_key: str) -> str:
    key_id, secret = admin_api_key.split(":", 1)
    header = json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":"))
    now = int(time.time())
    payload = json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":"))
    h, p = _b64url(header.encode()), _b64url(payload.encode())
    sig = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"

def ghost_headers():
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    return {
        "Authorization": f"Ghost {ghost_jwt(admin_api_key)}",
        "Content-Type": "application/json",
        "Accept-Version": "v5.0",
    }

# --- Lexical helpers ---

def text_node(text, bold=False, italic=False, code=False):
    fmt = 0
    if bold: fmt |= 1
    if italic: fmt |= 2
    if code: fmt |= 16
    return {"type": "text", "version": 1, "text": text, "format": fmt, "style": "", "detail": 0, "mode": "normal"}

def paragraph(children):
    if isinstance(children, str):
        children = [text_node(children)]
    return {"type": "paragraph", "version": 1, "format": "", "indent": 0, "direction": "ltr", "children": children}

def heading(text, tag="h2"):
    return {"type": "heading", "version": 1, "tag": tag, "format": "", "indent": 0, "direction": "ltr", "children": [text_node(text)]}

def bullet_list(items):
    return {
        "type": "list", "version": 1, "listType": "bullet", "start": 1, "tag": "ul",
        "format": "", "indent": 0, "direction": "ltr",
        "children": [
            {"type": "listitem", "version": 1, "value": i+1, "checked": False, "format": "", "indent": 0, "direction": "ltr", "children": [text_node(item)]}
            for i, item in enumerate(items)
        ],
    }

def html_card(html):
    return {"type": "html", "version": 1, "html": html}

def build_lexical(nodes):
    return json.dumps({"root": {"children": nodes, "direction": "ltr", "format": "", "indent": 0, "type": "root", "version": 1}}, ensure_ascii=False)


# --- Article generation ---

def generate_article(article_spec: dict) -> dict:
    """Generate a full article using Claude."""
    client = anthropic.Anthropic()

    prompt = f"""Write a comprehensive SEO article in Spanish for devaisemanal.com (a Spanish-language blog about AI development tools).

ARTICLE SPECS:
- Title: {article_spec['title']}
- Target keywords: {', '.join(article_spec['target_queries'])}
- Search intent: {article_spec['intent']}
- Meta description: {article_spec.get('meta_description', 'Generate one')}

REQUIREMENTS:
- Write in Spanish, professional but accessible tone
- 1500-2500 words
- Include practical examples and code snippets where relevant
- Structure with clear H2 and H3 headings
- Include a FAQ section at the end with 3-4 common questions
- Naturally incorporate target keywords
- Write for developers who want to learn about this tool/topic

OUTPUT FORMAT (JSON):
{{
    "meta_description": "155 chars max, compelling, includes primary keyword",
    "excerpt": "2-3 sentence summary for post cards",
    "sections": [
        {{
            "heading": "H2 heading text",
            "tag": "h2",
            "paragraphs": ["paragraph 1 text", "paragraph 2 text"],
            "bullets": ["optional", "bullet", "points"],
            "code_snippet": "optional code block"
        }}
    ],
    "faq": [
        {{"question": "FAQ question", "answer": "FAQ answer"}}
    ]
}}

Write the article now. Return ONLY valid JSON, no markdown wrappers."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    return json.loads(raw.strip())


def article_to_lexical(article_data: dict) -> list:
    """Convert generated article data to Lexical nodes."""
    nodes = []

    for section in article_data.get("sections", []):
        tag = section.get("tag", "h2")
        nodes.append(heading(section["heading"], tag))

        for para_text in section.get("paragraphs", []):
            nodes.append(paragraph(para_text))

        if section.get("bullets"):
            nodes.append(bullet_list(section["bullets"]))

        if section.get("code_snippet"):
            nodes.append(html_card(
                f'<pre style="background:#1e293b;color:#e2e8f0;padding:20px;border-radius:8px;overflow-x:auto;font-size:14px;line-height:1.6;"><code>{section["code_snippet"]}</code></pre>'
            ))

    # FAQ section
    if article_data.get("faq"):
        nodes.append(heading("Preguntas frecuentes", "h2"))
        for faq in article_data["faq"]:
            nodes.append(heading(faq["question"], "h3"))
            nodes.append(paragraph(faq["answer"]))

    # CTA
    nodes.append(html_card(CTA_HTML))

    return nodes


def publish_to_ghost(title: str, slug: str, lexical: str, meta_description: str, excerpt: str, tags: list[str]):
    """Publish a post to Ghost."""
    post_payload = {
        "posts": [{
            "title": title,
            "slug": slug,
            "status": "published",
            "lexical": lexical,
            "custom_excerpt": excerpt,
            "meta_title": title,
            "meta_description": meta_description,
            "tags": [{"name": t} for t in tags],
        }]
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{GHOST_URL}/ghost/api/admin/posts/",
            headers=ghost_headers(),
            json=post_payload,
        )
        if resp.status_code not in (200, 201):
            print(f"  ERROR {resp.status_code}: {resp.text[:300]}")
            return None
        data = resp.json()

    url = data["posts"][0]["url"]
    return url


# --- Articles to generate ---

ARTICLES_TO_GENERATE = [
    {
        "title": "Generadores de interfaces con IA: mejores herramientas para crear UI",
        "slug": "generadores-interfaces-ia-herramientas-ui",
        "target_queries": ["generador de interfaces ia", "generar ui con ia", "herramientas ia diseño interfaces"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "UI"],
    },
    {
        "title": "Amazon CodeWhisperer vs Amazon Q Developer: herramientas IA de AWS",
        "slug": "amazon-codewhisperer-vs-q-developer-ia-aws",
        "target_queries": ["amazon codewhisperer", "amazon q developer", "ia de aws como se llama", "amazon q"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "AWS"],
    },
    {
        "title": "Claude Code: terminal con IA que programa por ti (guía 2026)",
        "slug": "claude-code-terminal-ia-guia",
        "target_queries": ["claude code", "claude code terminal", "claude code guia", "programar con claude"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "Claude"],
    },
    {
        "title": "Los 10 mejores editores de código con IA en 2026",
        "slug": "mejores-editores-codigo-ia-2026",
        "target_queries": ["editores de codigo con ia", "mejores ide ia", "editor ia programar", "ide inteligencia artificial"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "Comparativas"],
    },
    {
        "title": "MCP (Model Context Protocol): qué es y cómo conectar tu IDE con IA",
        "slug": "mcp-model-context-protocol-guia",
        "target_queries": ["mcp protocol", "model context protocol", "mcp ia", "mcp servers"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "MCP"],
    },
    {
        "title": "Agentes de IA para programar: qué son y cómo funcionan",
        "slug": "agentes-ia-programar-guia",
        "target_queries": ["agentes ia programacion", "ai agents coding", "agentes inteligencia artificial programar"],
        "intent": "informational",
        "tags": ["Guías", "evergreen", "Agentes"],
    },
]


def main():
    print("=" * 60)
    print("  GENERATE & PUBLISH — DevAI SEO Articles")
    print("=" * 60)

    for i, spec in enumerate(ARTICLES_TO_GENERATE, 1):
        print(f"\n[{i}/{len(ARTICLES_TO_GENERATE)}] Generating: {spec['title']}")

        try:
            # Generate content
            article_data = generate_article(spec)
            print(f"  Content generated ({len(article_data.get('sections', []))} sections)")

            # Convert to Lexical
            nodes = article_to_lexical(article_data)
            lexical = build_lexical(nodes)

            # Publish
            url = publish_to_ghost(
                title=spec["title"],
                slug=spec["slug"],
                lexical=lexical,
                meta_description=article_data.get("meta_description", spec["title"]),
                excerpt=article_data.get("excerpt", ""),
                tags=spec["tags"],
            )

            if url:
                print(f"  PUBLISHED: {url}")
            else:
                print(f"  FAILED to publish")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

        # Small delay between articles
        time.sleep(2)

    print(f"\n{'=' * 60}")
    print("  Done!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
