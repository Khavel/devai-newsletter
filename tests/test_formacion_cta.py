import importlib.util
import json
import re
from pathlib import Path

import pytest

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
    # "tutoriales-claude-code-aceptar-automaticamente" sigue en CTA_TARGET_SLUGS (queda
    # constancia de que esta pendiente) pero replace_or_insert_cta lo salta por no tener
    # lexical -- no es uno de los slugs que de verdad recibe el CTA, así que el test ya no
    # lo exige. Los dos que sí se aplican de verdad son estos dos.
    assert "claude-code-dotnet-csharp-guia" in acciones.CTA_TARGET_SLUGS
    assert "claude-code-que-es-guia-completa" in acciones.CTA_TARGET_SLUGS
    assert len(acciones.CTA_TARGET_SLUGS) >= 5


class _FakeSurgery:
    """Stub de _ghost_cta_surgery.py para tests de capa de ejecucion: get_post fijo,
    put_post registra las llamadas sin tocar red."""

    def __init__(self, po, put_result=True):
        self._po = po
        self.put_calls = []
        self.put_result = put_result

    def get_post(self, slug):
        return self._po

    def put_post(self, post_id, body_posts):
        self.put_calls.append((post_id, body_posts))
        return self.put_result


def test_el_guard_anti_encogimiento_lanza_si_el_cuerpo_nuevo_es_mas_corto(monkeypatch, tmp_path):
    # Nodo cta-mid-article viejo deliberadamente enorme: al sustituirlo por CTA_FORMACION
    # (fijo, mucho mas corto) el lexical completo encoge -- el guard debe abortar ANTES de
    # backup o PUT.
    padded_old_cta_html = '<div id="cta-mid-article">' + ("x" * 5000) + "</div>"
    lex = {"root": {"children": [
        {"type": "heading"},
        {"type": "html", "html": padded_old_cta_html, "version": 1},
        {"type": "heading"},
    ]}}
    po = {"id": "abc123", "updated_at": "2026-09-16T00:00:00.000Z",
          "lexical": json.dumps(lex, ensure_ascii=False)}
    fake = _FakeSurgery(po)
    monkeypatch.setattr(acciones, "_surgery", lambda: fake)
    monkeypatch.setattr(acciones, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(acciones, "DRY", False)

    with pytest.raises(ValueError):
        acciones.replace_or_insert_cta("fake-slug-encoge")

    assert fake.put_calls == [], "el guard debe abortar antes de intentar el PUT"
    assert list(tmp_path.iterdir()) == [], "el guard debe abortar antes de escribir backup"


def test_post_sin_lexical_se_salta_y_no_escribe_backup(monkeypatch, tmp_path):
    po = {"id": "xyz789", "updated_at": "2026-09-16T00:00:00.000Z", "lexical": None}
    fake = _FakeSurgery(po)
    monkeypatch.setattr(acciones, "_surgery", lambda: fake)
    monkeypatch.setattr(acciones, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(acciones, "DRY", False)

    result = acciones.replace_or_insert_cta("fake-slug-sin-lexical")

    assert result == "skipped"
    assert fake.put_calls == []
    assert list(tmp_path.iterdir()) == []


def test_find_signup_cta_node_solo_cuenta_si_esta_en_la_mitad_o_antes():
    kids_con_cta_mid_article = [
        {"type": "heading"},
        {"type": "html", "html": '<div id="cta-mid-article">suscribete</div>', "version": 1},
        {"type": "paragraph"},
        {"type": "heading"},
        {"type": "paragraph"},
        {"type": "paragraph"},
    ]
    assert acciones._find_signup_cta_node(kids_con_cta_mid_article) == 1

    kids_sin_cta = [{"type": "heading"}, {"type": "paragraph"}, {"type": "paragraph"}]
    assert acciones._find_signup_cta_node(kids_sin_cta) is None

    # marcador presente pero DESPUES de la mitad -> no cuenta (se preferiria INSERT)
    kids_marcador_tarde = [
        {"type": "heading"},
        {"type": "paragraph"},
        {"type": "paragraph"},
        {"type": "paragraph"},
        {"type": "html", "html": '<div data-devai-signup-cta="1">x</div>', "version": 1},
    ]
    assert acciones._find_signup_cta_node(kids_marcador_tarde) is None
