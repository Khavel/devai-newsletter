import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_evergreen_articles.py"
SPEC = importlib.util.spec_from_file_location("publish_evergreen_articles", SCRIPT)
evergreen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evergreen)


def test_code_html_is_rendered_as_html_not_escaped_article_text():
    code = '<pre><code class="language-python">print("ok")</code></pre>'

    rendered = evergreen._html_paragraphs([code])

    assert "<pre>" in rendered
    assert "&lt;pre&gt;" not in rendered


def test_essay_sections_keep_code_html_as_a_code_card():
    code = '<pre><code class="language-javascript">console.log("ok")</code></pre>'

    nodes = evergreen.render_section("Ejemplo", [code], "essay")

    assert nodes[1]["type"] == "html"
    assert "&lt;pre&gt;" not in nodes[1]["html"]


def test_article_body_does_not_repeat_the_custom_excerpt_as_its_first_paragraph():
    spec = {
        "slug": "rendering-regression",
        "excerpt": "Este texto solo pertenece al extracto.",
        "sections": [("TL;DR", ["Este es el primer contenido útil."])],
    }

    nodes = evergreen.render_article_body(spec)

    assert nodes[0]["children"][0]["text"] == "Este es el primer contenido útil."


def test_publish_validation_rejects_escaped_code_markup():
    slug = "rendering-regression"
    html = (
        f'<a href="?utm_campaign={slug}">uno</a>'
        f'<a href="?utm_campaign={slug}">dos</a>'
        "<p>&lt;pre&gt;&lt;code&gt;broken&lt;/code&gt;&lt;/pre&gt;</p>"
    )

    ok, detail = evergreen.rendered_post_is_valid(html, slug, has_feature=True)

    assert not ok
    assert "escaped_code=True" in detail
