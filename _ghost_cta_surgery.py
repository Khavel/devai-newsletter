"""CTA surgery + credits-cluster fixes (2026-06-10 plan, Phase 2 + checker-corrected Phase 3).

1. Insert a mid-article CTA card (after the 2nd heading, ~30% depth) on the 5 top organic
   pages. Idempotent (marker id cta-mid-article). UTM BEFORE the '#'.
2. /tutoriales-claude-code-aceptar-automaticamente/ additionally gets a bottom CTA
   (it has none at all today).
3. Cross-link the two Copilot-credits pages (cluster block, both directions).
4. FAQ block on the credits HEAD page answering the literal GSC queries.
5. Intent-split retitle of the SECOND credits page only (head page title already optimized).

Dry-run by default; --apply to execute. Modeled on _ghost_internal_links.py.
"""
import sys, json, os, time, hashlib, hmac, base64
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
import httpx

admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
GHOST = "https://devaisemanal.com"
key_id, secret = admin_api_key.split(":", 1)


def token():
    now = int(time.time())
    def b(d): return base64.urlsafe_b64encode(d).decode().rstrip("=")
    h = b(json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":")).encode())
    p = b(json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":")).encode())
    s = hmac.new(bytes.fromhex(secret), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b(s)}"


def hdr():
    return {"Authorization": f"Ghost {token()}", "Accept-Version": "v5.0", "Content-Type": "application/json"}


SIGNUP = "https://devaisemanal.com/?utm_source=article&utm_medium=cta&utm_campaign=inline#/portal/signup"

CTA_MID = (
    '<div id="cta-mid-article" style="background:#f0f4ff;border-left:4px solid #4f46e5;'
    'padding:16px 20px;border-radius:8px;margin:28px 0">'
    '<p style="margin:0 0 12px;color:#333;font-weight:600">'
    "📬 Cada martes, las novedades de IA para devs en un email de 5 minutos.</p>"
    f'<a href="{SIGNUP}" '
    'style="background:#4f46e5;color:#fff;padding:8px 20px;border-radius:6px;'
    'text-decoration:none;font-weight:600;display:inline-block">Suscribete gratis</a>'
    "</div>"
)

CTA_BOTTOM = (
    '<div id="cta-bottom-article" style="background:#f0f4ff;border-left:4px solid #4f46e5;'
    'padding:20px;border-radius:8px;margin:32px 0">'
    '<p style="margin:0 0 8px;font-weight:600;font-size:1.1em">'
    "📬 ¿Quieres estar al día de las herramientas de IA para developers?</p>"
    '<p style="margin:0 0 16px;color:#444">'
    "Cada semana resumo las novedades más importantes en un email de 5 minutos.</p>"
    f'<a href="{SIGNUP}" '
    'style="background:#4f46e5;color:#fff;padding:10px 24px;border-radius:6px;'
    'text-decoration:none;font-weight:600;display:inline-block">Suscribirme gratis</a>'
    "</div>"
)

HEAD = "github-copilot-ai-credits-pago-por-uso"
CLI = "github-copilot-ai-credits-tokens-junio-2026"

CROSSLINK_ON_HEAD = (
    '<div id="cluster-credits-link" style="border:1px solid #e5e7eb;border-radius:8px;'
    'padding:14px 18px;margin:24px 0">'
    '<p style="margin:0;color:#333">Relacionado: '
    f'<a href="{GHOST}/{CLI}/">GitHub Copilot AI Credits desde la CLI: ver y controlar el gasto</a></p></div>'
)
CROSSLINK_ON_CLI = (
    '<div id="cluster-credits-link" style="border:1px solid #e5e7eb;border-radius:8px;'
    'padding:14px 18px;margin:24px 0">'
    '<p style="margin:0;color:#333">Relacionado: '
    f'<a href="{GHOST}/{HEAD}/">GitHub Copilot AI Credits: cuánto cuestan y cómo no pasarte</a></p></div>'
)

FAQ_ON_HEAD = (
    '<section id="faq-credits">'
    "<h2>Preguntas frecuentes sobre los AI Credits de GitHub Copilot</h2>"
    "<h3>¿Cuánto cuestan los AI credits?</h3>"
    "<p>Cada plan de Copilot incluye una cuota mensual de premium requests; al agotarla, "
    "cada request premium adicional se factura aparte segun el multiplicador del modelo. "
    "Los modelos mas potentes consumen mas credits por peticion.</p>"
    "<h3>¿Cómo se calculan por modelo?</h3>"
    "<p>Cada modelo tiene un multiplicador: una peticion a un modelo con multiplicador 1 "
    "consume 1 premium request; un modelo con multiplicador superior consume proporcionalmente "
    "mas. El detalle por modelo esta en la tabla de este articulo.</p>"
    "<h3>¿Qué pasa cuando se agotan?</h3>"
    "<p>Puedes seguir usando el modelo base incluido sin coste extra, activar la facturacion "
    "por uso con un limite de gasto, o esperar al reinicio mensual de la cuota.</p>"
    "<h3>¿Cómo veo mi consumo desde la CLI?</h3>"
    f'<p>Se puede consultar y controlar el gasto desde la linea de comandos: lo explicamos paso '
    f'a paso en <a href="{GHOST}/{CLI}/">la guia de AI credits desde la CLI</a>.</p>'
    "</section>"
)

# meta retitle for the CLI page ONLY (head page already optimized, checker-verified)
CLI_META = {
    "meta_title": "GitHub Copilot AI Credits: controlar el gasto desde la CLI (junio 2026)",
    "meta_description": (
        "Como ver y controlar el consumo de AI credits de GitHub Copilot desde la CLI: "
        "comandos, limites de gasto y que hacer cuando se agotan los premium requests."
    ),
}

MID_CTA_PAGES = [
    "github-copilot-ai-credits-pago-por-uso",
    "tutoriales-claude-code-aceptar-automaticamente",
    "v0-dev-generar-ui-ia",
    "rtk-proxy-cli-reducir-tokens-ia",
    "github-copilot-ai-credits-tokens-junio-2026",
]

DRY = "--apply" not in sys.argv


def get_post(slug):
    r = httpx.get(
        f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?formats=lexical&fields=id,updated_at,lexical,meta_title,meta_description,title",
        headers=hdr(), timeout=30)
    r.raise_for_status()
    return r.json()["posts"][0]


def put_post(post_id, body_posts):
    u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{post_id}/", headers=hdr(),
                  json={"posts": [body_posts]}, timeout=30)
    print(f"  -> PUT {u.status_code}" + ("" if u.status_code == 200 else f" :: {u.text[:300]}"))
    return u.status_code == 200


def insert_html_via_html_source(slug, marker, html, position):
    """Fallback for posts without lexical: edit the HTML body via ?source=html."""
    r = httpx.get(
        f"{GHOST}/ghost/api/admin/posts/slug/{slug}/?formats=html&fields=id,updated_at,html",
        headers=hdr(), timeout=30)
    r.raise_for_status()
    po = r.json()["posts"][0]
    body = po["html"] or ""
    if marker in body:
        print(f"  SKIP {slug}: {marker} already present (html)")
        return True
    if position == "mid":
        # insert before the 2nd <h2 (i.e. after the first section's body)
        first = body.find("<h2")
        second = body.find("<h2", first + 1) if first != -1 else -1
        pos = second if second != -1 else len(body) // 3
    else:
        pos = len(body)
    print(f"  {slug}: insert {marker} at html offset {pos}/{len(body)} (html-source path)")
    if DRY:
        print("  [DRY RUN]")
        return True
    new_html = body[:pos] + html + body[pos:]
    u = httpx.put(f"{GHOST}/ghost/api/admin/posts/{po['id']}/?source=html", headers=hdr(),
                  json={"posts": [{"updated_at": po["updated_at"], "html": new_html}]}, timeout=30)
    print(f"  -> PUT {u.status_code}" + ("" if u.status_code == 200 else f" :: {u.text[:300]}"))
    return u.status_code == 200


def insert_html_node(slug, marker, html, position):
    """position: 'mid' (after 2nd heading), 'tail' (before trailing html cards), 'end'."""
    po = get_post(slug)
    if not po.get("lexical"):
        return insert_html_via_html_source(slug, marker, html, position)
    if marker in (po["lexical"] or ""):
        print(f"  SKIP {slug}: {marker} already present")
        return True
    lex = json.loads(po["lexical"])
    kids = lex["root"]["children"]
    node = {"type": "html", "html": html, "version": 1}
    if position == "mid":
        heads = [i for i, c in enumerate(kids) if c.get("type") == "heading"]
        idx = (heads[1] if len(heads) >= 2 else heads[0] if heads else max(1, len(kids) // 3))
        # insert right BEFORE the 2nd heading => after the first section's body (~30% depth)
        pos = idx
    elif position == "tail":
        pos = len(kids)
        while pos > 0 and kids[pos - 1].get("type") == "html":
            pos -= 1
    else:
        pos = len(kids)
    print(f"  {slug}: insert {marker} at index {pos}/{len(kids)}")
    if DRY:
        print("  [DRY RUN]")
        return True
    kids.insert(pos, node)
    return put_post(po["id"], {"updated_at": po["updated_at"], "lexical": json.dumps(lex, ensure_ascii=False)})


def main():
    print("== 1. mid-article CTA on 5 top organic pages ==")
    for slug in MID_CTA_PAGES:
        insert_html_node(slug, "cta-mid-article", CTA_MID, "mid")

    print("\n== 2. bottom CTA on the tutoriales page (has none) ==")
    insert_html_node("tutoriales-claude-code-aceptar-automaticamente", "cta-bottom-article", CTA_BOTTOM, "end")

    print("\n== 3. credits cluster cross-links ==")
    insert_html_node(HEAD, "cluster-credits-link", CROSSLINK_ON_HEAD, "tail")
    insert_html_node(CLI, "cluster-credits-link", CROSSLINK_ON_CLI, "tail")

    print("\n== 4. FAQ on the credits head page ==")
    insert_html_node(HEAD, "faq-credits", FAQ_ON_HEAD, "tail")

    print("\n== 5. intent-split retitle of the CLI credits page ==")
    po = get_post(CLI)
    print(f"  current meta_title: {po.get('meta_title')!r}")
    print(f"  new     meta_title: {CLI_META['meta_title']!r}")
    if not DRY:
        put_post(po["id"], {"updated_at": po["updated_at"], **CLI_META})
    else:
        print("  [DRY RUN]")

    print("\nDRY RUN. Re-run with --apply." if DRY else "\nDONE.")


if __name__ == "__main__":
    main()
