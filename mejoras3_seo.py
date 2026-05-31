"""
Mejoras batch devaisemanal.com — ronda 3 (SEO On-Page)
  1. SoftwareApplication JSON-LD schema en páginas de herramientas
  2. FAQ schema en guías con sección de preguntas frecuentes
  3. Meta descriptions optimizadas (reducir keyword stuffing)
  4. Semantic enrichment: añadir palabras clave semánticas al contenido
  5. Legibility: párrafos más cortos, más H2/H3, TL;DR boxes
"""
import hashlib, hmac, json, os, time, base64, re
import httpx

GHOST_URL     = os.environ.get("GHOST_URL", "https://devaisemanal.com")
ADMIN_API_KEY = os.environ["GHOST_ADMIN_API_KEY"]


def ghost_jwt():
    key_id, secret_hex = ADMIN_API_KEY.split(":")
    secret = bytes.fromhex(secret_hex)
    now = int(time.time())
    header  = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    payload = {"iat": now, "exp": now + 300, "aud": "/admin/"}
    def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
    h = b64(json.dumps(header,  separators=(",", ":")).encode())
    p = b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64(sig)}"


def hdrs():
    return {"Authorization": f"Ghost {ghost_jwt()}", "Content-Type": "application/json", "Accept-Version": "v5.0"}


# ─── 1. SoftwareApplication JSON-LD ──────────────────────────────────────────

SOFTWARE_SCHEMAS = {
    "guias-claude-code": {
        "name": "Claude Code",
        "description": "Agente de programación basado en IA de Anthropic que opera desde la terminal. Lee, modifica y ejecuta código de forma autónoma.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows (WSL)",
        "offers": {"@type": "Offer", "price": "20", "priceCurrency": "USD", "description": "Plan Pro desde $20/mes"},
        "creator": {"@type": "Organization", "name": "Anthropic", "url": "https://anthropic.com"},
    },
    "claude-code-que-es-guia-completa": {
        "name": "Claude Code",
        "description": "Herramienta CLI de Anthropic para programación asistida por IA. Agente autónomo que puede leer, editar y ejecutar código.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows (WSL)",
        "offers": {"@type": "Offer", "price": "20", "priceCurrency": "USD", "description": "Plan Pro desde $20/mes"},
        "creator": {"@type": "Organization", "name": "Anthropic", "url": "https://anthropic.com"},
    },
    "cursor-ai-que-es-guia-completa": {
        "name": "Cursor AI",
        "description": "IDE basado en VS Code con IA integrada para desarrollo de software. Incluye autocompletado, chat y agente Composer.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "20", "priceCurrency": "USD", "description": "Plan Pro desde $20/mes, tier gratuito disponible"},
        "creator": {"@type": "Organization", "name": "Anysphere", "url": "https://cursor.com"},
    },
    "github-copilot-guia-completa": {
        "name": "GitHub Copilot",
        "description": "Asistente de programación con IA de GitHub que ofrece autocompletado inteligente y chat integrado en editores de código.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "10", "priceCurrency": "USD", "description": "Individual desde $10/mes, Business $19/mes"},
        "creator": {"@type": "Organization", "name": "GitHub", "url": "https://github.com"},
    },
    "guias-mcp-servers": {
        "name": "Model Context Protocol (MCP)",
        "description": "Protocolo abierto de Anthropic para conectar modelos de IA con herramientas y servicios externos. Estándar universal de integración.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Protocolo open source gratuito"},
        "creator": {"@type": "Organization", "name": "Anthropic", "url": "https://anthropic.com"},
    },
    "guias-vibe-coding": {
        "name": "Vibe Coding",
        "description": "Paradigma de programación donde describes lo que quieres en lenguaje natural y la IA genera el código. Popularizado por Andrej Karpathy.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Multiplataforma",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Concepto — herramientas individuales tienen sus propios precios"},
        "creator": {"@type": "Organization", "name": "Comunidad", "url": "https://devaisemanal.com"},
    },
    "comparativas-claude-code-vs-cursor": {
        "name": "Claude Code vs Cursor AI",
        "description": "Comparativa detallada entre Claude Code (CLI agent) y Cursor AI (IDE agent) para desarrollo con IA en 2026.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "20", "priceCurrency": "USD", "description": "Ambas herramientas desde $20/mes"},
        "creator": {"@type": "Organization", "name": "DevAI Semanal", "url": "https://devaisemanal.com"},
    },
    "comparativas-mejor-ia-programar": {
        "name": "Mejor IA para programar",
        "description": "Ranking completo de herramientas de IA para programación en 2026: Claude Code, Cursor, Copilot, Bolt, Replit y más.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Multiplataforma",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Precios varían por herramienta"},
        "creator": {"@type": "Organization", "name": "DevAI Semanal", "url": "https://devaisemanal.com"},
    },
    "tabnine-autocompletado-codigo-ia": {
        "name": "Tabnine",
        "description": "Asistente de autocompletado de código con IA que funciona en local. Soporta múltiples lenguajes y se integra con los principales editores.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "12", "priceCurrency": "USD", "description": "Pro desde $12/mes, tier gratuito disponible"},
        "creator": {"@type": "Organization", "name": "Tabnine", "url": "https://tabnine.com"},
    },
    "windsurf-ide-editor-ia": {
        "name": "Windsurf",
        "description": "Editor de código con IA integrada de Codeium. Fork de VS Code con agente Cascade para desarrollo asistido por IA.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Tier gratuito disponible, Pro desde $10/mes"},
        "creator": {"@type": "Organization", "name": "Codeium", "url": "https://codeium.com"},
    },
    "replit-programar-navegador-ia": {
        "name": "Replit",
        "description": "Entorno de desarrollo en el navegador con IA integrada. Permite crear, ejecutar y desplegar aplicaciones sin configuración local.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Navegador web (multiplataforma)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Tier gratuito, Core desde $20/mes"},
        "creator": {"@type": "Organization", "name": "Replit", "url": "https://replit.com"},
    },
    "bolt-new-crear-apps-ia-navegador": {
        "name": "Bolt.new",
        "description": "Plataforma para crear aplicaciones web completas en el navegador usando IA. Genera fullstack apps desde prompts en lenguaje natural.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Navegador web (multiplataforma)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Tier gratuito, Pro desde $20/mes"},
        "creator": {"@type": "Organization", "name": "StackBlitz", "url": "https://bolt.new"},
    },
    "v0-dev-generar-ui-ia": {
        "name": "v0.dev",
        "description": "Generador de interfaces de usuario con IA de Vercel. Crea componentes React/Next.js desde descripciones en lenguaje natural.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Navegador web (multiplataforma)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Tier gratuito, Premium desde $20/mes"},
        "creator": {"@type": "Organization", "name": "Vercel", "url": "https://vercel.com"},
    },
    "amazon-q-developer-ia-aws": {
        "name": "Amazon Q Developer",
        "description": "Asistente de desarrollo con IA de AWS. Genera código, responde preguntas técnicas y automatiza tareas de desarrollo en el ecosistema AWS.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Tier gratuito disponible, Pro $19/mes"},
        "creator": {"@type": "Organization", "name": "Amazon Web Services", "url": "https://aws.amazon.com"},
    },
    "amazon-codewhisperer-vs-q-developer-ia-aws": {
        "name": "Amazon CodeWhisperer vs Q Developer",
        "description": "Comparativa entre Amazon CodeWhisperer y Amazon Q Developer: evolución, diferencias y cuál usar para desarrollo con IA en AWS.",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS, Linux, Windows",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "Q Developer incluye CodeWhisperer, tier gratuito disponible"},
        "creator": {"@type": "Organization", "name": "Amazon Web Services", "url": "https://aws.amazon.com"},
    },
}


def build_software_jsonld(slug, info):
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": info["name"],
        "description": info["description"],
        "applicationCategory": info["applicationCategory"],
        "operatingSystem": info["operatingSystem"],
        "offers": info["offers"],
        "author": info["creator"],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


# ─── 2. FAQ Schema from existing content ─────────────────────────────────────

def extract_faq_from_html(html):
    """Extract Q&A pairs from HTML content that has h3 questions followed by p answers."""
    faqs = []
    pattern = re.compile(r'<h3[^>]*>\s*([^<]*\?)\s*</h3>\s*<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
    for match in pattern.finditer(html):
        question = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        answer = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if question and answer and len(answer) > 20:
            faqs.append({"question": question, "answer": answer})
    return faqs


def build_faq_jsonld(faqs):
    if not faqs:
        return None
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                }
            }
            for faq in faqs
        ]
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


# ─── 3. Meta description optimization ────────────────────────────────────────

META_UPDATES = {
    "guias-claude-code": {
        "meta_description": "Guía completa de Claude Code en español: instalación, workflow, slash commands, hooks, integración MCP y comparativa con Cursor y Copilot. Actualizada a 2026.",
        "meta_title": "Claude Code: Guía Definitiva para Desarrolladores (2026)",
    },
    "claude-code-que-es-guia-completa": {
        "meta_description": "Descubre qué es Claude Code y cómo usarlo en tu día a día. Guía práctica con instalación, comandos esenciales y workflow para desarrolladores.",
        "meta_title": "Qué es Claude Code — Guía Completa para Desarrolladores (2026)",
    },
    "cursor-ai-que-es-guia-completa": {
        "meta_description": "Cursor AI explicado para desarrolladores: qué es, cómo funciona su agente Composer, precios y cuándo elegirlo frente a VS Code + Copilot.",
        "meta_title": "Cursor AI: Qué es y Cómo Usarlo — Guía para Desarrolladores (2026)",
    },
    "github-copilot-guia-completa": {
        "meta_description": "GitHub Copilot en profundidad: autocompletado, chat, Agent Mode, precios y cómo aprovecharlo al máximo en VS Code, JetBrains y Neovim.",
        "meta_title": "GitHub Copilot: Guía Completa para Desarrolladores (2026)",
    },
    "guias-mcp-servers": {
        "meta_description": "Model Context Protocol (MCP) explicado: arquitectura, los mejores servidores, cómo crear el tuyo y cómo conectarlo con Claude Code. Guía técnica en español.",
        "meta_title": "MCP (Model Context Protocol): Guía Completa (2026)",
    },
    "guias-vibe-coding": {
        "meta_description": "Qué es vibe coding, cómo adoptarlo sin perder el control del código y qué herramientas usar. Guía práctica con ejemplos reales para desarrolladores.",
        "meta_title": "Vibe Coding: Qué es y Cómo Programar con IA (2026)",
    },
    "comparativas-claude-code-vs-cursor": {
        "meta_description": "Claude Code vs Cursor AI: comparativa objetiva para desarrolladores. Terminal vs IDE, agente autónomo vs colaborativo, precios y cuándo usar cada uno.",
        "meta_title": "Claude Code vs Cursor AI: Comparativa Completa (2026)",
    },
    "comparativas-mejor-ia-programar": {
        "meta_description": "Ranking de las mejores herramientas de IA para programar en 2026: Claude Code, Cursor, Copilot, Bolt, Replit, v0 y más. Comparativa honesta con precios.",
        "meta_title": "Mejor IA para Programar en 2026 — Ranking Completo",
    },
    "tutoriales-claude-code-hooks": {
        "meta_description": "Aprende a configurar Claude Code Hooks: automatiza linting, tests y notificaciones con eventos PostToolUse y Stop. Ejemplos reales y settings.json completo.",
        "meta_title": "Claude Code Hooks: Automatiza tu Workflow de Desarrollo (2026)",
    },
    "tutoriales-claude-code-aceptar-automaticamente": {
        "meta_description": "Cómo hacer que Claude Code acepte ediciones y comandos sin pedir confirmación. Modo auto-edits, Shift+Tab, settings.json y flag --dangerously-skip-permissions.",
        "meta_title": "Claude Code: Aceptar Todo Automáticamente — Tutorial (2026)",
    },
    "claude-sonnet-opus-haiku": {
        "meta_description": "Diferencias entre Claude Sonnet, Opus y Haiku explicadas para desarrolladores: cuándo usar cada modelo, precios, velocidad y calidad de código.",
        "meta_title": "Claude Sonnet vs Opus vs Haiku: Guía de Modelos (2026)",
    },
    "tabnine-autocompletado-codigo-ia": {
        "meta_description": "Tabnine en profundidad: autocompletado local con IA, modelos on-premise, integración con editores, precios y comparativa con Copilot y Cursor.",
        "meta_title": "Tabnine: Autocompletado de Código con IA — Guía Completa (2026)",
    },
    "windsurf-ide-editor-ia": {
        "meta_description": "Windsurf (Codeium) analizado: editor IA con agente Cascade, autocompletado gratuito, comparativa con Cursor y cuándo elegirlo para tu workflow.",
        "meta_title": "Windsurf IDE: Editor de Código con IA — Análisis Completo (2026)",
    },
    "replit-programar-navegador-ia": {
        "meta_description": "Replit para desarrolladores: IDE en el navegador con IA, deploy instantáneo, colaboración en tiempo real. Precios, limitaciones y casos de uso.",
        "meta_title": "Replit: Programar en el Navegador con IA — Guía Completa (2026)",
    },
    "bolt-new-crear-apps-ia-navegador": {
        "meta_description": "Bolt.new explicado: crea aplicaciones web completas desde un prompt. Cómo funciona, limitaciones, precios y cuándo usarlo frente a Replit o v0.",
        "meta_title": "Bolt.new: Crear Apps con IA en el Navegador — Guía (2026)",
    },
    "v0-dev-generar-ui-ia": {
        "meta_description": "v0.dev de Vercel analizado: genera componentes React y Next.js con IA desde texto. Cómo funciona, calidad del código, precios y alternativas.",
        "meta_title": "v0.dev: Generar UI con IA — Guía para Desarrolladores (2026)",
    },
    "amazon-q-developer-ia-aws": {
        "meta_description": "Amazon Q Developer explicado: el asistente IA de AWS para generar código, resolver dudas técnicas y automatizar tareas de desarrollo cloud.",
        "meta_title": "Amazon Q Developer: IA para Desarrollo en AWS — Guía (2026)",
    },
    "amazon-codewhisperer-vs-q-developer-ia-aws": {
        "meta_description": "CodeWhisperer vs Q Developer: qué cambió, cuál es la evolución y qué herramienta de IA usar para desarrollo en AWS en 2026.",
        "meta_title": "Amazon CodeWhisperer vs Q Developer — Comparativa (2026)",
    },
}


# ─── 4. Semantic enrichment keywords per page ────────────────────────────────

SEMANTIC_KEYWORDS = {
    "guias-claude-code": [
        "agente de programación", "terminal IA", "CLI inteligente", "pair programming",
        "refactorización automática", "code review IA", "desarrollo asistido",
    ],
    "cursor-ai-que-es-guia-completa": [
        "IDE inteligente", "editor de código IA", "VS Code fork", "Composer agent",
        "autocompletado avanzado", "programación asistida", "pair programming IA",
    ],
    "github-copilot-guia-completa": [
        "autocompletado IA", "sugerencias de código", "pair programmer", "code completion",
        "IntelliSense IA", "productividad desarrollo", "GitHub integration",
    ],
    "guias-mcp-servers": [
        "protocolo abierto", "integración IA", "herramientas externas", "API estándar",
        "servidor MCP", "cliente MCP", "extensibilidad", "conectores IA",
    ],
    "guias-vibe-coding": [
        "programación natural language", "IA generativa código", "prototipado rápido",
        "Andrej Karpathy", "agente autónomo", "productividad developer",
    ],
}


# ─── 5. Legibility: TL;DR boxes ──────────────────────────────────────────────

TLDR_BOXES = {
    "guias-claude-code": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">Claude Code es un agente de terminal de Anthropic que lee, edita y ejecuta código de forma autónoma. Necesitas Node.js 18+ y plan Pro ($20/mes). Instala con <code>npm install -g @anthropic-ai/claude-code</code>, navega a tu proyecto y ejecuta <code>claude</code>. Usa <code>/model</code> para cambiar entre Sonnet (rápido) y Opus (potente).</p>
</div>""",
    "cursor-ai-que-es-guia-completa": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">Cursor es un IDE basado en VS Code con IA integrada: autocompletado, chat contextual y un agente (Composer) que puede editar múltiples archivos. Tier gratuito disponible, Pro desde $20/mes. Ideal si prefieres trabajar en un editor visual en vez del terminal.</p>
</div>""",
    "github-copilot-guia-completa": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">GitHub Copilot es el asistente de código más extendido: autocompletado en línea, chat en el editor y Agent Mode para tareas complejas. Funciona en VS Code, JetBrains, Neovim y más. Individual $10/mes, Business $19/mes.</p>
</div>""",
    "guias-mcp-servers": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">MCP es el protocolo abierto de Anthropic para conectar IAs con herramientas externas (bases de datos, GitHub, Slack…). Es como un USB-C universal para agentes de IA. Añade servidores con <code>claude mcp add</code> y Claude Code los usa automáticamente.</p>
</div>""",
    "guias-vibe-coding": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">Vibe coding = describir lo que quieres en lenguaje natural y dejar que la IA escriba el código. Popularizado por Karpathy en 2025, hoy lo practican millones de devs con Claude Code, Cursor y Bolt. Potente para prototipos; requiere supervisión para producción.</p>
</div>""",
    "claude-code-que-es-guia-completa": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">Claude Code es el agente CLI de Anthropic: le das instrucciones en lenguaje natural y él lee, edita y ejecuta código. Plan Pro $20/mes, instala con <code>npm install -g @anthropic-ai/claude-code</code>. Sonnet para tareas rápidas, Opus para las complejas.</p>
</div>""",
    "cursor-ai-que-es-guia-completa": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">Cursor AI es un fork de VS Code con IA nativa: autocompletado, chat y agente Composer para ediciones multi-archivo. Tier gratuito disponible, Pro $20/mes. Ideal si prefieres IDE visual sobre terminal.</p>
</div>""",
    "github-copilot-guia-completa": """<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:16px 20px;margin:0 0 32px 0;border-radius:4px;">
<p style="margin:0 0 8px 0;font-weight:700;color:#166534;">TL;DR</p>
<p style="margin:0;color:#374151;line-height:1.6;">GitHub Copilot ofrece autocompletado inteligente, chat y Agent Mode en VS Code, JetBrains y Neovim. El más extendido para código IA. Individual $10/mes, Business $19/mes, Enterprise $39/mes.</p>
</div>""",
}


# ─── Execution ────────────────────────────────────────────────────────────────

def fetch_all_content():
    """Fetch all posts and pages from Ghost with full content fields."""
    all_items = []
    for content_type in ("posts", "pages"):
        page = 1
        while True:
            time.sleep(0.5)
            with httpx.Client(timeout=30) as c:
                r = c.get(
                    f"{GHOST_URL}/ghost/api/admin/{content_type}/"
                    f"?fields=id,slug,title,lexical,mobiledoc,codeinjection_head,meta_title,meta_description,updated_at"
                    f"&formats=html&limit=50&page={page}",
                    headers=hdrs(),
                )
                r.raise_for_status()
            data = r.json()
            items = data.get(content_type, [])
            if not items:
                break
            for item in items:
                item["_type"] = content_type
            all_items.extend(items)
            meta = data.get("meta", {}).get("pagination", {})
            if page >= meta.get("pages", 1):
                break
            page += 1
    return all_items


def apply_schema_markup(items):
    """Add SoftwareApplication + FAQ JSON-LD to codeinjection_head."""
    print("\n[1] Añadiendo Schema Markup (JSON-LD)…")
    updated = 0

    for item in items:
        slug = item["slug"]
        schemas_to_add = []

        if slug in SOFTWARE_SCHEMAS and "SoftwareApplication" not in (item.get("codeinjection_head") or ""):
            schemas_to_add.append(build_software_jsonld(slug, SOFTWARE_SCHEMAS[slug]))

        html = item.get("html") or ""
        if "?" in html and "FAQPage" not in (item.get("codeinjection_head") or ""):
            faqs = extract_faq_from_html(html)
            if faqs:
                faq_ld = build_faq_jsonld(faqs)
                if faq_ld:
                    schemas_to_add.append(faq_ld)

        if not schemas_to_add:
            continue

        existing_head = item.get("codeinjection_head") or ""
        new_head = existing_head + "\n" + "\n".join(schemas_to_add)

        endpoint = "posts" if item["_type"] == "posts" else "pages"
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.put(
                f"{GHOST_URL}/ghost/api/admin/{endpoint}/{item['id']}/",
                headers=hdrs(),
                json={endpoint: [{"codeinjection_head": new_head.strip(), "updated_at": item["updated_at"]}]},
            )
        if r.status_code in (200, 201):
            item["updated_at"] = r.json()[endpoint][0]["updated_at"]
            what = []
            if slug in SOFTWARE_SCHEMAS:
                what.append("SoftwareApp")
            if any("FAQPage" in s for s in schemas_to_add):
                what.append("FAQ")
            print(f"  ✓ {slug} — {' + '.join(what)}")
            updated += 1
        else:
            print(f"  ✗ Error {r.status_code} en {slug}: {r.text[:200]}")

    print(f"  → {updated} páginas actualizadas con schema")
    return items


def apply_meta_updates(items):
    """Update meta_title and meta_description for keyword stuffing reduction."""
    print("\n[2] Optimizando meta descriptions…")
    updated = 0

    for item in items:
        slug = item["slug"]
        if slug not in META_UPDATES:
            continue

        changes = META_UPDATES[slug]
        needs_update = False
        payload = {"updated_at": item["updated_at"]}

        for field in ("meta_title", "meta_description"):
            if field in changes and item.get(field) != changes[field]:
                payload[field] = changes[field]
                needs_update = True

        if not needs_update:
            print(f"  ⚠ Ya optimizado: {slug}")
            continue

        endpoint = "posts" if item["_type"] == "posts" else "pages"
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.put(
                f"{GHOST_URL}/ghost/api/admin/{endpoint}/{item['id']}/",
                headers=hdrs(),
                json={endpoint: [payload]},
            )
        if r.status_code in (200, 201):
            item["updated_at"] = r.json()[endpoint][0]["updated_at"]
            print(f"  ✓ {slug}")
            updated += 1
        else:
            print(f"  ✗ Error {r.status_code} en {slug}: {r.text[:200]}")

    print(f"  → {updated} metas actualizados")
    return items


def _inject_tldr_mobiledoc(mobiledoc_str, tldr_html):
    """Inject TL;DR HTML card into mobiledoc after the first card (which is usually the intro)."""
    md = json.loads(mobiledoc_str)
    cards = md.get("cards", [])
    if not cards:
        return None

    main_html = cards[0][1].get("html", "")
    hr_pos = main_html.find("<hr")
    if hr_pos != -1:
        hr_end = main_html.find(">", hr_pos)
        if hr_end != -1:
            hr_end += 1
            main_html = main_html[:hr_end] + "\n\n" + tldr_html + "\n\n" + main_html[hr_end:]
    else:
        intro_end = main_html.find("</p>")
        if intro_end != -1:
            intro_end += 4
            main_html = main_html[:intro_end] + "\n\n" + tldr_html + "\n\n" + main_html[intro_end:]
        else:
            main_html = tldr_html + "\n\n" + main_html

    cards[0][1]["html"] = main_html
    md["cards"] = cards
    return json.dumps(md)


def _inject_tldr_lexical(lexical_str, tldr_html):
    """Inject TL;DR as an HTML card node into lexical after the first horizontal-rule."""
    lex = json.loads(lexical_str)
    children = lex.get("root", {}).get("children", [])
    if not children:
        return None

    tldr_node = {"type": "html", "version": 1, "html": tldr_html}

    insert_at = None
    for i, child in enumerate(children):
        if child.get("type") == "horizontalrule" or child.get("tag") == "hr":
            insert_at = i + 1
            break

    if insert_at is None:
        for i, child in enumerate(children):
            if child.get("type") == "paragraph":
                insert_at = i + 1
                break

    if insert_at is None:
        insert_at = 0

    children.insert(insert_at, tldr_node)
    lex["root"]["children"] = children
    return json.dumps(lex)


def apply_tldr_boxes(items):
    """Insert TL;DR summary box into guides (handles both mobiledoc and lexical)."""
    print("\n[3] Añadiendo TL;DR boxes…")
    updated = 0

    for item in items:
        slug = item["slug"]
        if slug not in TLDR_BOXES:
            continue

        html = item.get("html") or ""
        if "TL;DR" in html:
            print(f"  ⚠ Ya tiene TL;DR: {slug}")
            continue

        tldr = TLDR_BOXES[slug]
        payload = {"updated_at": item["updated_at"]}

        if item.get("lexical"):
            new_lex = _inject_tldr_lexical(item["lexical"], tldr)
            if new_lex:
                payload["lexical"] = new_lex
            else:
                print(f"  ⚠ No se pudo inyectar en lexical: {slug}")
                continue
        elif item.get("mobiledoc"):
            new_mob = _inject_tldr_mobiledoc(item["mobiledoc"], tldr)
            if new_mob:
                payload["mobiledoc"] = new_mob
            else:
                print(f"  ⚠ No se pudo inyectar en mobiledoc: {slug}")
                continue
        else:
            print(f"  ⚠ Sin formato editable: {slug}")
            continue

        endpoint = "posts" if item["_type"] == "posts" else "pages"
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.put(
                f"{GHOST_URL}/ghost/api/admin/{endpoint}/{item['id']}/",
                headers=hdrs(),
                json={endpoint: [payload]},
            )
        if r.status_code in (200, 201):
            resp_item = r.json()[endpoint][0]
            item["updated_at"] = resp_item["updated_at"]
            item["html"] = resp_item.get("html", html)
            fmt = "lexical" if "lexical" in payload else "mobiledoc"
            print(f"  ✓ {slug} ({fmt})")
            updated += 1
        else:
            print(f"  ✗ Error {r.status_code} en {slug}: {r.text[:200]}")

    print(f"  → {updated} TL;DR boxes añadidos")
    return items


def print_summary(items):
    """Print a summary of all content with SEO status."""
    print("\n" + "=" * 60)
    print("RESUMEN SEO — devaisemanal.com")
    print("=" * 60)
    for item in items:
        head = item.get("codeinjection_head") or ""
        has_sw = "SoftwareApplication" in head
        has_faq = "FAQPage" in head
        has_tldr = "TL;DR" in (item.get("html") or "")
        has_meta = item["slug"] in META_UPDATES

        status = []
        if has_sw:
            status.append("✓Schema")
        if has_faq:
            status.append("✓FAQ")
        if has_tldr:
            status.append("✓TL;DR")
        if has_meta:
            status.append("✓Meta")

        if status:
            print(f"  {item['slug']:50s} {' '.join(status)}")

    print("=" * 60)


if __name__ == "__main__":
    print("Descargando contenido de Ghost…")
    items = fetch_all_content()
    print(f"  Encontrados: {len(items)} items ({sum(1 for i in items if i['_type']=='pages')} pages, {sum(1 for i in items if i['_type']=='posts')} posts)")

    items = apply_schema_markup(items)
    items = apply_meta_updates(items)
    items = apply_tldr_boxes(items)
    print_summary(items)

    print("\n✅ Mejoras SEO completadas.")
