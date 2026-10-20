"""Crispy form buttons read the layered button class table."""

import re

import pytest
from django.template import Template
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.test import override_settings
from django.urls import reverse

from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.settings import CrudViewsSettings


def url(viewset, key, pk=None) -> str:
    kwargs = {"pk": pk} if pk is not None else {}
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def tag(html: str, **attrs) -> str:
    """The first <input ...> tag carrying all the given attributes."""
    for match in re.finditer(r"<input\b[^>]*>", html):
        found = match.group(0)
        if all(f'{k}="{v}"' in found for k, v in attrs.items()):
            return found
    raise AssertionError(f"no input with {attrs} in page")


@pytest.mark.django_db
def test_submit_and_cancel_classes(client_user_author_add, cv_author):
    html = client_user_author_add.get(url(cv_author, "create")).content.decode()
    assert 'class="btn btn-primary"' in tag(html, name="submit")
    assert 'class="btn btn-secondary"' in tag(html, name="reset")
    assert "btn btn btn-secondary" not in html


@pytest.mark.django_db
def test_delete_button_hook(client_user_author_delete, cv_author, author_douglas_adams, monkeypatch, settings):
    from tests.test1.app.views import AuthorDeleteView

    target = url(cv_author, "delete", author_douglas_adams.pk)
    html = client_user_author_delete.get(target).content.decode()
    button = tag(html, name="delete")
    assert 'class="btn btn-primary"' in button
    assert 'value="Delete"' in button

    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:delete": "btn btn-danger"}):
        html = client_user_author_delete.get(target).content.decode()
    assert 'class="btn btn-danger"' in tag(html, name="delete")

    class EraseForm(CrispyDeleteForm):
        def get_delete_button_kwargs(self) -> dict:
            return {"name": "delete", "value": "Erase"}

    monkeypatch.setattr(AuthorDeleteView, "form_class", EraseForm)
    html = client_user_author_delete.get(target).content.decode()
    assert 'value="Erase"' in tag(html, name="delete")


@pytest.mark.django_db
def test_filter_buttons(client_user_publisher_view, cv_publisher):
    html = client_user_publisher_view.get(url(cv_publisher, "list")).content.decode()
    assert 'class="btn btn-primary"' in tag(html, id="filter-button")
    reset = tag(html, id="filter-button-reset")
    assert 'class="btn btn-secondary"' in reset
    assert 'type="reset"' in reset
    assert "btn-inverse" not in html


@pytest.mark.django_db
def test_project_css_class_still_appended(client_user_author_add, cv_author, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm

    class ExtraForm(AuthorForm):
        def get_cancel_button_kwargs(self) -> dict:
            return {**super().get_cancel_button_kwargs(), "css_class": "extra"}

    monkeypatch.setattr(AuthorCreateView, "form_class", ExtraForm)
    html = client_user_author_add.get(url(cv_author, "create")).content.decode()
    assert 'class="btn btn-secondary extra"' in tag(html, name="reset")


def test_filter_reset_setting_removed():
    assert not hasattr(CrudViewsSettings(), "filter_reset_button_css_class")


def test_removed_tags():
    with pytest.raises(TemplateSyntaxError):
        Template("{% load crud_views %}{% cv_cancel_button %}")
    with pytest.raises(TemplateDoesNotExist):
        get_template("crud_views/tags/button_cancel.html")
