"""Phase 06.21 / #339: instance snippets see the view and, on a child ViewSet, the lazy parent object."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.db import connection
from django.http import Http404
from django.template import Context, Template
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils.functional import SimpleLazyObject

from crud_views.lib.table import LinkChildColumn
from crud_views.lib.table.table import TableWithViewContext
from crud_views.lib.view import ContextButton
from crud_views.lib.view.base import CrudView
from tests.test1.app.models import Author
from tests.test1.app.views import (
    AuthorCreateView,
    AuthorDetailView,
    AuthorPingView,
    BookCreateView,
    BookListView,
    PublisherListView,
)


def _make_view(view_class, **url_kwargs):
    """A view instance set up for one GET request (as Django's as_view() would before dispatch)."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    view = view_class()
    view.setup(request, **url_kwargs)
    return view


def _publisher_queries(captured) -> list[str]:
    return [q["sql"] for q in captured.captured_queries if "app_publisher" in q["sql"]]


def _messages(response) -> list[str]:
    return [m.message for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
def test_e2e_create_header_renders_parent_object(client_user_book_add, publisher_penguin, monkeypatch):
    monkeypatch.setattr(BookCreateView, "cv_header_template_code", "New book for {{ parent_object }}")
    response = client_user_book_add.get(f"/publisher/{publisher_penguin.pk}/book/create/")
    assert response.status_code == 200
    assert f"New book for {publisher_penguin}" in response.content.decode()


@pytest.mark.django_db
def test_e2e_action_message_renders_view_attribute(client_user_author_change, monkeypatch):
    author = Author.objects.create(first_name="First", last_name="Author")

    def action(self, context):
        self.duplicate = "DRAFT-42"
        return True

    monkeypatch.setattr(AuthorPingView, "action", action)
    monkeypatch.setattr(AuthorPingView, "cv_message_template_code", "Created {{ view.duplicate }} from {{ object }}")
    response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    assert _messages(response) == [f"Created DRAFT-42 from {author}"]


@pytest.mark.django_db
def test_meta_exposes_view_and_lazy_parent_object_on_child_view(publisher_penguin):
    view = _make_view(BookCreateView, publisher_pk=publisher_penguin.pk)
    with CaptureQueriesContext(connection) as captured:
        data = view.cv_get_meta()
    assert len(captured.captured_queries) == 0  # building the dict resolves nothing
    assert data["view"] is view
    assert "parent_object" in data
    # free only because it succeeds on type(); a failing isinstance falls back to __class__ and resolves the proxy
    assert isinstance(data["parent_object"], SimpleLazyObject)
    assert data["parent_object"] == publisher_penguin
    assert data["parent_object"].pk == publisher_penguin.pk


@pytest.mark.django_db
def test_meta_has_no_parent_object_on_top_level_view():
    view = _make_view(AuthorCreateView)
    data = view.cv_get_meta()
    assert data["view"] is view
    assert "parent_object" not in data
    assert Template("[{{ parent_object }}]").render(Context(data)) == "[]"
    for key in ("request", "user", "ancestors"):
        assert key not in data


@pytest.mark.django_db
def test_meta_keeps_object_key_unchanged(author_douglas_adams):
    view = _make_view(AuthorCreateView)
    data = view.cv_get_meta()
    assert data["object"] is None  # ViewContext.to_dict() always seeds the key
    view.object = author_douglas_adams
    assert view.cv_get_meta()["object"] is author_douglas_adams


@pytest.mark.django_db
def test_filter_header_snippet_sees_view_and_parent_object(publisher_penguin, monkeypatch):
    template = "Filter {{ view.cv_key }} for {{ parent_object }}"
    monkeypatch.setattr(BookListView, "cv_filter_header_template_code", template)
    view = _make_view(BookListView, publisher_pk=publisher_penguin.pk)
    assert view.cv_filter_header == f"Filter list for {publisher_penguin}"


@pytest.mark.django_db
def test_lazy_parent_object_is_not_resolved_when_unreferenced(publisher_penguin, monkeypatch):
    calls = []
    original = CrudView.cv_get_parent_object

    def spy(self):
        calls.append(self)
        return original(self)

    monkeypatch.setattr(CrudView, "cv_get_parent_object", spy)
    view = _make_view(BookCreateView, publisher_pk=publisher_penguin.pk)
    view.render_snippet(view.cv_get_meta(), template_code="New book")
    assert calls == []
    result = view.render_snippet(view.cv_get_meta(), template_code="New book for {{ parent_object }}")
    assert len(calls) == 1
    assert result == f"New book for {publisher_penguin}"


@pytest.mark.django_db
def test_query_free_header_paragraph_and_message_on_dispatched_view(user_book_add, publisher_penguin, monkeypatch):
    pk = publisher_penguin.pk
    path = f"/publisher/{pk}/book/create/"
    request = RequestFactory().get(path)
    request.user = user_book_add
    view = BookCreateView()
    view.setup(request, publisher_pk=pk)
    assert view.dispatch(request, publisher_pk=pk).status_code == 200

    monkeypatch.setattr(BookCreateView, "cv_header_template_code", "New book for {{ parent_object }}")
    monkeypatch.setattr(BookCreateView, "cv_paragraph_template_code", "Publisher: {{ parent_object.name }}")
    monkeypatch.setattr(BookCreateView, "cv_message_template_code", "Created {{ object }} for {{ parent_object }}")
    error_template = "Could not create a book for {{ parent_object }}"
    monkeypatch.setattr(BookCreateView, "cv_message_template_error_code", error_template)
    with CaptureQueriesContext(connection) as captured:
        results = [
            view.cv_header,
            view.cv_paragraph,
            view.cv_get_message(),
            view.cv_get_message(error=True),
        ]
    assert _publisher_queries(captured) == []
    for result in results:
        assert "Penguin" in result


@pytest.mark.django_db
def test_query_delta_is_zero_when_header_and_paragraph_reference_parent_object(
    client_user_book_add, publisher_penguin, monkeypatch
):
    path = f"/publisher/{publisher_penguin.pk}/book/create/"
    with CaptureQueriesContext(connection) as before:
        assert client_user_book_add.get(path).status_code == 200
    monkeypatch.setattr(BookCreateView, "cv_header_template_code", "New book for {{ parent_object }}")
    monkeypatch.setattr(BookCreateView, "cv_paragraph_template_code", "Publisher: {{ parent_object.name }}")
    with CaptureQueriesContext(connection) as after:
        response = client_user_book_add.get(path)
    assert response.status_code == 200
    assert f"New book for {publisher_penguin}" in response.content.decode()
    # SC-2 is the Publisher-table delta; total counts include session/auth/permission queries and are not compared
    assert len(_publisher_queries(after)) == len(_publisher_queries(before))


@pytest.mark.django_db
def test_label_class_level_action_label_does_not_see_view(publisher_penguin):
    class Labelled(AuthorCreateView):
        cv_action_label_template_code = "x{{ view }}y"

    assert Labelled.cv_get_action_label(context=_make_view(AuthorCreateView).cv_get_view_context()) == "xy"

    class ChildLabelled(BookCreateView):
        cv_action_label_template_code = "x{{ view }}{{ parent_object }}y"

    child_context = _make_view(BookCreateView, publisher_pk=publisher_penguin.pk).cv_get_view_context()
    assert ChildLabelled.cv_get_action_label(context=child_context) == "xy"


@pytest.mark.django_db
def test_context_button_own_label_uses_button_data_not_snippet_variables(author_douglas_adams):
    view = _make_view(AuthorDetailView, pk=author_douglas_adams.pk)
    view.object = author_douglas_adams
    view.request.resolver_match = resolve(f"/author/{author_douglas_adams.pk}/detail/")
    button = ContextButton(
        key="home",
        key_target="list",
        label_template_code=(
            "[VN:{{ verbose_name }}][VS:{{ viewset }}][O:{{ object }}]"
            "[K:{{ cv_key }}][V:{{ view }}][P:{{ parent_object }}]"
        ),
    )
    data = button.get_context(view.cv_get_view_context())
    assert data["cv_action_label"] == "[VN:][VS:][O:][K:list][V:][P:]"


@pytest.mark.django_db
@pytest.mark.parametrize("supply_parent", [False, True])
def test_link_child_column_inherits_hosting_page_context(publisher_penguin, supply_parent):
    view = _make_view(PublisherListView)
    column = LinkChildColumn(
        name="book",
        template_code=("[V:{{ view.cv_key }}][P:{{ parent_object }}][O:{{ object }}][VN:{{ verbose_name_plural }}]"),
    )
    table = TableWithViewContext([publisher_penguin], view=view, extra_columns=[("books", column)])
    page_context = {"table": table, "view": view}
    if supply_parent:
        page_context["parent_object"] = publisher_penguin
    rendered = Template("{% load django_tables2 %}{% render_table table %}").render(Context(page_context))
    expected_parent = str(publisher_penguin) if supply_parent else ""
    assert f"[V:list][P:{expected_parent}][O:None][VN:Books]" in rendered


@pytest.mark.django_db
def test_http404_propagates_for_missing_parent_without_guard_state():
    view = _make_view(BookCreateView, publisher_pk=999999)
    data = view.cv_get_meta()
    with pytest.raises(Http404):
        Template("{{ parent_object }}").render(Context(data))
