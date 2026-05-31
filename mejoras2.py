"""
Mejoras batch devaisemanal.com — ronda 2
  1. Navegación — añadir /archivo y Guías
  2. Featured images en los 3 artículos
  3. About page con contenido real
  4. Internal linking (sección "También te puede interesar")
"""
import hashlib, hmac, json, os, time, base64
import httpx

GHOST_URL     = os.environ.get("GHOST_URL", "https://devaisemanal.com")
ADMIN_API_KEY = os.environ["GHOST_ADMIN_API_KEY"]

def ghost_jwt():
    key_id, secret_hex = ADMIN_API_KEY.split(":")
    secret = bytes.fromhex(secret_hex)
    now = int(time.time())
    header  = {"alg":"HS256","typ":"JWT","kid":key_id}
    payload = {"iat":now,"exp":now+300,"aud":"/admin/"}
    def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
    h = b64(json.dumps(header,  separators=(",",":")).encode())
    p = b64(json.dumps(payload, separators=(",",":")).encode())
    sig = hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64(sig)}"

def hdrs():
    return {"Authorization": f"Ghost {ghost_jwt()}", "Content-Type": "application/json", "Accept-Version": "v5.0"}

def lexical(children):
    return json.dumps({"root":{"type":"root","version":1,"format":"","indent":0,"direction":"ltr","children":children}})

def para(text):
    return {"type":"paragraph","version":1,"format":"","indent":0,"direction":"ltr",
            "children":[{"type":"text","version":1,"text":text,"format":0,"style":"","detail":0,"mode":"normal"}]}

def h2(text):
    return {"type":"heading","version":1,"tag":"h2","format":"","indent":0,"direction":"ltr",
            "children":[{"type":"text","version":1,"text":text,"format":0,"style":"","detail":0,"mode":"normal"}]}

def h3(text):
    return {"type":"heading","version":1,"tag":"h3","format":"","indent":0,"direction":"ltr",
            "children":[{"type":"text","version":1,"text":text,"format":0,"style":"","detail":0,"mode":"normal"}]}

def ul(items):
    return {"type":"list","version":1,"listType":"bullet","start":1,"tag":"ul","format":"","indent":0,"direction":"ltr",
            "children":[{"type":"listitem","version":1,"value":i+1,"checked":False,"format":"","indent":0,"direction":"ltr",
                         "children":[{"type":"text","version":1,"text":it,"format":0,"style":"","detail":0,"mode":"normal"}]}
                        for i,it in enumerate(items)]}

def html_card(html):
    return {"type":"html","version":1,"html":html}

CTA_HTML = """<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:32px;margin:40px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:20px;font-weight:700;margin:0 0 8px;color:#0c4a6e;">¿Te ha resultado útil este artículo?</p>
  <p style="font-size:15px;color:#374151;margin:0 0 24px;line-height:1.6;">Cada martes publico las mejores herramientas de IA para desarrolladores.<br>Claude Code, Cursor, Copilot, MCP… todo en español y con contexto real. Gratis.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis →</a>
</div>"""

# ─── 1. Navegación ────────────────────────────────────────────────────────────
def update_navigation():
    print("\n[1] Actualizando navegación…")
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{GHOST_URL}/ghost/api/admin/settings/", headers=hdrs())
        r.raise_for_status()

    settings = {s["key"]: s["value"] for s in r.json()["settings"]}
    nav = json.loads(settings.get("navigation", "[]"))

    labels = [n["label"] for n in nav]
    added = []

    if "Guías" not in labels:
        nav.append({"label": "Guías", "url": "/tag/guias/"})
        added.append("Guías → /tag/guias/")
    if "Archivo" not in labels:
        nav.append({"label": "Archivo", "url": "/archivo/"})
        added.append("Archivo → /archivo/")

    if not added:
        print("  ⚠ Navegación ya actualizada")
        return

    time.sleep(1)
    with httpx.Client(timeout=30) as c:
        r = c.put(
            f"{GHOST_URL}/ghost/api/admin/settings/",
            headers=hdrs(),
            json={"settings": [{"key": "navigation", "value": json.dumps(nav)}]}
        )
        if r.status_code not in (200, 201):
            print(f"  ✗ Error {r.status_code}: {r.text[:300]}")
            return
    print(f"  ✓ Añadido: {', '.join(added)}")


# ─── 2. Featured images ───────────────────────────────────────────────────────
FEATURED_IMAGES = {
    "claude-code-que-es-guia-completa": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=1200&h=628&fit=crop&q=80",
    "cursor-ai-que-es-guia-completa":   "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&h=628&fit=crop&q=80",
    "github-copilot-guia-completa":     "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=1200&h=628&fit=crop&q=80",
}

def add_featured_images():
    print("\n[2] Añadiendo featured images…")
    for slug, img_url in FEATURED_IMAGES.items():
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{GHOST_URL}/ghost/api/admin/posts/?filter=slug:{slug}&fields=id,feature_image,updated_at", headers=hdrs())
            r.raise_for_status()
        posts = r.json().get("posts", [])
        if not posts:
            print(f"  ✗ No encontrado: {slug}")
            continue
        post = posts[0]
        if post.get("feature_image"):
            print(f"  ⚠ Ya tiene imagen: {slug}")
            continue

        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.put(
                f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
                headers=hdrs(),
                json={"posts": [{"feature_image": img_url, "updated_at": post["updated_at"]}]}
            )
        if r.status_code in (200, 201):
            print(f"  ✓ {slug}")
        else:
            print(f"  ✗ Error {r.status_code} en {slug}: {r.text[:200]}")


# ─── 3. About page ────────────────────────────────────────────────────────────
def update_about_page():
    print("\n[3] Actualizando página About…")

    # Find the About page
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{GHOST_URL}/ghost/api/admin/pages/?filter=slug:about&fields=id,updated_at", headers=hdrs())
        r.raise_for_status()
    pages = r.json().get("pages", [])

    children = [
        para("DevAI Semanal es una newsletter semanal sobre herramientas de inteligencia artificial para desarrolladores, en español. Cada martes seleccionamos y analizamos las 5-7 noticias más relevantes del ecosistema: nuevas herramientas, actualizaciones de modelos, proyectos en GitHub y tendencias que importan si escribes código."),

        h2("¿Qué encontrarás aquí?"),
        ul([
            "Novedades de Claude, Cursor, GitHub Copilot, Windsurf y el resto de herramientas de IA para devs",
            "Análisis de nuevos modelos y lo que significan en la práctica para el trabajo diario",
            "Proyectos open source interesantes de GitHub Trending relacionados con IA y desarrollo",
            "Todo en español, con contexto real — no traducción de titulares",
        ]),

        h2("El pipeline"),
        para("DevAI Semanal funciona con un pipeline completamente automatizado: cada martes a las 9:00h (España) un proceso recoge noticias de RSS, Hacker News, Reddit y GitHub Trending, Claude selecciona y redacta las mejores, y el resultado se publica aquí y se envía por email a los suscriptores — sin intervención manual."),
        para("El código del pipeline es open source en GitHub."),

        h2("Quién hay detrás"),
        para("Soy Alejandro Oceja, desarrollador y entusiasta de las herramientas de IA. Uso Claude Code, Cursor y GitHub Copilot a diario en mi trabajo, y empecé DevAI Semanal porque no encontraba una fuente en español que cubriera estas herramientas con la profundidad que merecen."),

        h2("Suscríbete"),
        html_card("""<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:32px;margin:32px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:18px;font-weight:700;margin:0 0 8px;color:#0c4a6e;">Un martes a la semana, nada más.</p>
  <p style="font-size:15px;color:#374151;margin:0 0 24px;">Sin spam. Sin contenido diario. Solo lo que merece tu atención esa semana.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis →</a>
</div>"""),
    ]

    payload = {
        "title":            "Sobre DevAI Semanal",
        "lexical":          lexical(children),
        "meta_title":       "Sobre DevAI Semanal — newsletter de IA para desarrolladores",
        "meta_description": "DevAI Semanal es una newsletter semanal en español sobre herramientas de IA para desarrolladores: Claude, Cursor, Copilot, MCP y más.",
    }

    time.sleep(1)
    if pages:
        page_id = pages[0]["id"]
        payload["updated_at"] = pages[0]["updated_at"]
        with httpx.Client(timeout=30) as c:
            r = c.put(f"{GHOST_URL}/ghost/api/admin/pages/{page_id}/", headers=hdrs(), json={"pages": [payload]})
        action = "actualizada"
    else:
        payload.update({"slug": "about", "status": "published"})
        with httpx.Client(timeout=30) as c:
            r = c.post(f"{GHOST_URL}/ghost/api/admin/pages/", headers=hdrs(), json={"pages": [payload]})
        action = "creada"

    if r.status_code in (200, 201):
        print(f"  ✓ About page {action}")
    else:
        print(f"  ✗ Error {r.status_code}: {r.text[:300]}")


# ─── 4. Internal linking ──────────────────────────────────────────────────────
RELATED = {
    "claude-code-que-es-guia-completa": {
        "others": [
            {"title": "Cursor AI: qué es y cómo usarlo en 2025", "url": "/cursor-ai-que-es-guia-completa/"},
            {"title": "GitHub Copilot: guía completa para desarrolladores (2025)", "url": "/github-copilot-guia-completa/"},
        ]
    },
    "cursor-ai-que-es-guia-completa": {
        "others": [
            {"title": "Qué es Claude Code: guía completa para desarrolladores (2026)", "url": "/claude-code-que-es-guia-completa/"},
            {"title": "GitHub Copilot: guía completa para desarrolladores (2025)", "url": "/github-copilot-guia-completa/"},
        ]
    },
    "github-copilot-guia-completa": {
        "others": [
            {"title": "Qué es Claude Code: guía completa para desarrolladores (2026)", "url": "/claude-code-que-es-guia-completa/"},
            {"title": "Cursor AI: qué es y cómo usarlo en 2025", "url": "/cursor-ai-que-es-guia-completa/"},
        ]
    },
}

def make_related_html(others):
    links = "".join(
        f'<a href="https://devaisemanal.com{o["url"]}" style="display:block;padding:12px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;text-decoration:none;color:#1e293b;font-weight:500;font-size:14px;margin-bottom:8px;">→ {o["title"]}</a>'
        for o in others
    )
    return f"""<div style="margin:40px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:13px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin:0 0 12px;">También te puede interesar</p>
  {links}
</div>"""

def add_internal_links():
    print("\n[4] Añadiendo internal links…")
    for slug, data in RELATED.items():
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{GHOST_URL}/ghost/api/admin/posts/?filter=slug:{slug}&fields=id,lexical,updated_at", headers=hdrs())
            r.raise_for_status()
        posts = r.json().get("posts", [])
        if not posts:
            print(f"  ✗ No encontrado: {slug}")
            continue

        post = posts[0]
        lex  = json.loads(post["lexical"])
        children = lex["root"]["children"]

        # Check if already has related section
        if any(c.get("type") == "html" and "También te puede interesar" in c.get("html","") for c in children):
            print(f"  ⚠ Ya tiene links: {slug}")
            continue

        # Insert related links BEFORE the CTA (which is the last html card with portal/signup)
        related_card = html_card(make_related_html(data["others"]))
        cta_idx = None
        for i in range(len(children)-1, -1, -1):
            if children[i].get("type") == "html" and "portal/signup" in children[i].get("html",""):
                cta_idx = i
                break

        if cta_idx is not None:
            children.insert(cta_idx, related_card)
        else:
            children.append(related_card)

        lex["root"]["children"] = children
        time.sleep(1)
        with httpx.Client(timeout=30) as c:
            r = c.put(
                f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
                headers=hdrs(),
                json={"posts": [{"lexical": json.dumps(lex), "updated_at": post["updated_at"]}]}
            )
        if r.status_code in (200, 201):
            print(f"  ✓ {slug}")
        else:
            print(f"  ✗ Error {r.status_code} en {slug}: {r.text[:200]}")


if __name__ == "__main__":
    update_navigation()
    add_featured_images()
    update_about_page()
    add_internal_links()
    print("\n✅ Todo completado.")
