"""
Create canonical URL page on Ghost for the Dev.to article.
This page at /como-automatice-newsletter-ia-developers/ serves as the
canonical_url target so Dev.to passes link equity back to devaisemanal.com.
"""
import hashlib, hmac, json, os, time, base64
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


SLUG = "como-automatice-newsletter-ia-developers"

PAGE_HTML = """<h1>Cómo automaticé una newsletter de IA para developers con Claude API y GitHub Actions</h1>

<p>Este artículo explica paso a paso cómo construí <strong>DevAI Semanal</strong>, una newsletter completamente automatizada que cada martes recoge, filtra y redacta las noticias más relevantes sobre herramientas de IA para desarrolladores — en español.</p>

<h2>El pipeline completo</h2>

<p>El sistema tiene 5 fases que se ejecutan automáticamente en GitHub Actions:</p>

<ol>
<li><strong>Sourcing</strong>: Recoge noticias de RSS (Anthropic, OpenAI, GitHub), Hacker News, Reddit y GitHub Trending.</li>
<li><strong>Curation</strong>: Claude API selecciona los 5-7 items más relevantes usando criterios editoriales estrictos.</li>
<li><strong>Rewriting</strong>: Claude reescribe cada noticia en español con contexto práctico y opinión.</li>
<li><strong>Assembly</strong>: Renderiza el HTML del newsletter (compatible con email clients).</li>
<li><strong>Publishing</strong>: Publica en Ghost CMS + envía por MailerLite + notifica por Telegram.</li>
</ol>

<h2>Stack técnico</h2>

<ul>
<li>Python + httpx para el pipeline</li>
<li>Claude API (claude-sonnet-4-20250514) para curación y redacción</li>
<li>Ghost CMS en Fly.io para el archivo web</li>
<li>MailerLite para el envío de emails</li>
<li>GitHub Actions como scheduler (cron cada martes 07:00 UTC)</li>
</ul>

<h2>Características clave</h2>

<ul>
<li><strong>Idempotencia</strong>: Cada fase guarda su output como JSON. Si el pipeline falla, al relanzarlo continúa donde se quedó.</li>
<li><strong>Rate limiting defensivo</strong>: 0.5 req/s para APIs públicas, 1 req/s para Claude. Meses sin un solo ban.</li>
<li><strong>Fuentes configurables</strong>: Todo parametrizado en YAML. Añadir una fuente es editar un fichero.</li>
<li><strong>Open source</strong>: El código completo está disponible en GitHub.</li>
</ul>

<h2>Lee el artículo completo</h2>

<p>Publiqué una versión extendida de este artículo en Dev.to con código de ejemplo, prompts completos, y lecciones aprendidas sobre HTML para email, prompt engineering, y automatización con GitHub Actions.</p>

<p>→ <a href="/guias-claude-code/">Guía completa de Claude Code</a></p>
<p>→ <a href="/guias-mcp-servers/">Guía de MCP Servers</a></p>
<p>→ <a href="/guias-vibe-coding/">Guía de Vibe Coding</a></p>

<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:32px;margin:40px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:20px;font-weight:700;margin:0 0 8px;color:#0c4a6e;">¿Te ha resultado útil?</p>
  <p style="font-size:15px;color:#374151;margin:0 0 24px;line-height:1.6;">Cada martes publico las mejores herramientas de IA para desarrolladores.<br>Claude Code, Cursor, Copilot, MCP… todo en español y con contexto real. Gratis.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis →</a>
</div>"""


def create_canonical_page():
    print("Checking if page already exists...")
    with httpx.Client(timeout=30) as c:
        r = c.get(
            f"{GHOST_URL}/ghost/api/admin/posts/?filter=slug:{SLUG}&fields=id,slug,updated_at",
            headers=hdrs()
        )
        r.raise_for_status()
    posts = r.json().get("posts", [])

    if posts:
        print(f"Page already exists at /{SLUG}/ (id: {posts[0]['id']})")
        return

    # Also check pages endpoint
    time.sleep(1)
    with httpx.Client(timeout=30) as c:
        r = c.get(
            f"{GHOST_URL}/ghost/api/admin/pages/?filter=slug:{SLUG}&fields=id,slug,updated_at",
            headers=hdrs()
        )
        r.raise_for_status()
    pages = r.json().get("pages", [])

    if pages:
        print(f"Page already exists at /{SLUG}/ (id: {pages[0]['id']})")
        return

    # Create as a post (better for SEO — gets indexed, shows in sitemap, has tags)
    mobiledoc = json.dumps({
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": PAGE_HTML}]],
        "markups": [],
        "sections": [[10, 0]]
    })

    payload = {
        "posts": [{
            "title": "Cómo automaticé una newsletter de IA para developers con Claude API y GitHub Actions",
            "slug": SLUG,
            "mobiledoc": mobiledoc,
            "status": "published",
            "tags": [{"name": "guias"}, {"name": "automatizacion"}, {"name": "claude-api"}],
            "meta_title": "Cómo Automaticé una Newsletter de IA para Developers | DevAI Semanal",
            "meta_description": "Pipeline open source con Claude API y GitHub Actions que recoge noticias de IA, las cura y redacta en español cada semana. Código y arquitectura completos.",
            "og_title": "Cómo automaticé una newsletter de IA para developers",
            "og_description": "Pipeline completo con Claude API + GitHub Actions: sourcing, curación, redacción en español y publicación automática cada martes.",
            "feature_image": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80",
        }]
    }

    time.sleep(1)
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{GHOST_URL}/ghost/api/admin/posts/", headers=hdrs(), json=payload)

    if r.status_code in (200, 201):
        new_slug = r.json()["posts"][0]["slug"]
        print(f"Created post at /{new_slug}/")
    else:
        print(f"Error {r.status_code}: {r.text[:500]}")


if __name__ == "__main__":
    create_canonical_page()
