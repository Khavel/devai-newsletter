import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("acciones", ROOT / "_ghost_seo_actions_2026_09_16.py")
acciones = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acciones)


def test_los_retitulos_caben_en_la_serp_y_llevan_la_keyword_al_principio():
    esperados = {
        "tabnine": r"^tabnine",
        "bolt-new": r"^bolt\.new",
        "playwright-mcp": r"^playwright mcp",
        "v0": r"^v0",
        "mcp-inspector": r"^mcp inspector",
    }
    vistos = set()
    for slug, title, desc in acciones.RETITLES:
        assert len(title) <= 60, (slug, len(title))
        assert 120 <= len(desc) <= 160, (slug, len(desc))
        for clave, patron in esperados.items():
            if clave in slug:
                assert re.match(patron, title, re.I), (slug, title)
                vistos.add(clave)
    assert vistos == set(esperados), f"faltan retítulos para {set(esperados) - vistos}"


def test_el_cta_de_formacion_es_idempotente_y_no_vende_suscripcion():
    html = acciones.CTA_FORMACION
    assert 'id="cta-formacion"' in html
    assert "devaisemanal.com/formacion/" in html
    assert "utm_campaign=formacion" in html
    assert "suscr" not in html.lower()
    assert "sin compromiso" not in html.lower()


def test_la_pagina_de_formacion_no_nombra_al_empleador_ni_promete_plazas():
    html = acciones.FORMACION_PAGE["html"].lower()
    for prohibido in ("bestsecret", "best secret", "plazas limitadas", "últimas plazas"):
        assert prohibido not in html
    assert acciones.FORMACION_PAGE["slug"] == "formacion"
    assert "linkedin.com/in/alejandrooceja" in html
    assert "a.oceja.dev@gmail.com" in html


def test_los_destinos_del_cta_son_las_guias_de_claude_code_y_dotnet():
    assert "claude-code-dotnet-csharp-guia" in acciones.CTA_TARGET_SLUGS
    assert "tutoriales-claude-code-aceptar-automaticamente" in acciones.CTA_TARGET_SLUGS
    assert len(acciones.CTA_TARGET_SLUGS) >= 5
