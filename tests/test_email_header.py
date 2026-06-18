from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]


def _render():
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    t = env.get_template("newsletter.html.j2")
    return t.render(
        newsletter={"name": "DevAI Semanal", "tagline": "IA para devs",
                    "logo_url": "https://devaisemanal.com/content/images/logo-light.png"},
        date_display="18 jun 2026", intro="Hola", articles=[],
    )


def test_header_has_logo_image():
    html = _render()
    assert "<img" in html and "logo-light.png" in html


def test_link_color_is_indigo():
    html = _render()
    assert "#4F46E5" in html
