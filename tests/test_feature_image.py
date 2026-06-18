import importlib

from src import publishing


def test_feature_image_is_branded_not_unsplash():
    importlib.reload(publishing)
    assert "unsplash" not in publishing._NEWSLETTER_FEATURE_IMAGE.lower()
    assert "devaisemanal.com" in publishing._NEWSLETTER_FEATURE_IMAGE


def test_feature_image_env_override(monkeypatch):
    monkeypatch.setenv("DEVAI_FEATURE_IMAGE", "https://devaisemanal.com/content/images/x.png")
    importlib.reload(publishing)
    assert publishing._NEWSLETTER_FEATURE_IMAGE.endswith("x.png")
