import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import translation


def _render(langs):
    rf = RequestFactory()
    request = rf.get("/some/path/")
    tmpl = Template("{% load crud_views %}{% cv_language_selector %}")
    with translation.override("de"):
        with pytest.MonkeyPatch().context() as mp:
            from django.conf import settings

            mp.setattr(settings, "LANGUAGES", langs, raising=False)
            return tmpl.render(Context({"request": request}))


def test_selector_lists_languages_and_posts_to_set_language():
    html = _render([("en", "English"), ("de", "German"), ("zh-hans", "Simplified Chinese")])
    assert "set_language" in html or "/i18n/setlang" in html  # form action resolves
    assert "English" in html and "German" in html
    assert 'value="/some/path/"' in html  # next=current path
    assert 'value="zh-hans"' in html  # language code offered


def test_selector_hidden_for_single_language():
    html = _render([("en", "English")])
    assert html.strip() == ""
