"""Class-level labels on pydantic config objects accept gettext_lazy and stay lazy.

FormSet / CardAction instances are built at import time; coercing a lazy string to ``str`` there
would freeze it in the server's startup language.
"""

import pytest
from django.test.client import Client
from django.utils import translation
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy
from lxml import html
from pydantic import BaseModel, ValidationError

from crud_views.lib.formsets import FormSet
from crud_views.lib.lazy import LazyStr
from crud_views.lib.view import CardAction
from tests.test1.app.views_formset import BookFormSet


class _Model(BaseModel):
    text: LazyStr


def test_lazy_str_keeps_promise_unevaluated():
    lazy = gettext_lazy("Delete")
    assert _Model(text=lazy).text is lazy
    assert _Model(text="plain").text == "plain"


def test_lazy_str_rejects_non_strings():
    with pytest.raises(ValidationError):
        _Model(text=42)


def test_object_detail_reexports_core_lazy_str():
    from crud_views_object_detail.lib.config import LazyStr as od_lazy_str

    assert od_lazy_str is LazyStr


def test_formset_title_accepts_lazy_string():
    lazy = gettext_lazy("Books")
    formset = FormSet(title=lazy, klass=BookFormSet)
    assert isinstance(formset.title, Promise)
    assert formset.title is lazy


def test_card_action_label_accepts_lazy_string():
    lazy = gettext_lazy("Delete")
    assert CardAction(key="delete", label=lazy).label is lazy


@pytest.mark.django_db
def test_card_action_lazy_label_renders_in_active_language(
    client: Client, user_author_view, author_douglas_adams, monkeypatch
):
    from tests.test1.app.views import AuthorCardListView

    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label=gettext_lazy("Delete"))])
    client.force_login(user_author_view)

    with translation.override("de"):
        response = client.get("/author/card/")
    assert response.status_code == 200
    labels = [s.text_content().strip() for s in html.fromstring(response.content).cssselect(".card.mb-3 a span")]
    assert "Löschen" in labels
