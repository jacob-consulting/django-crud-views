"""The display budget is applied after visibility, independently of deletion authority."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from crud_views.lib.deletion import DeleteInspection, RelatedObjects
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views import DeleteView

SHORTENED = "This preview is shortened. Additional objects are not shown."


@pytest.fixture
def preview_view(publisher_penguin, user_publisher_cascade_delete):
    from django.test import RequestFactory

    from tests.test1.app.views import PublisherCascadeDeleteView

    view = PublisherCascadeDeleteView()
    request = RequestFactory().get("/preview/")
    request.user = user_publisher_cascade_delete
    view.setup(request, pk=publisher_penguin.pk)
    view.object = publisher_penguin
    view.cv_filter_related_objects = lambda user, related: related
    return view


@pytest.mark.django_db
def test_delete_preview_selection_budget(preview_view):
    from tests.test1.app.models import Contract

    first, second = Contract(title="First"), Contract(title="Second")
    view = preview_view
    view.cv_delete_preview_limit = 1
    view._cv_inspect_deletion = lambda: DeleteInspection(RelatedObjects([view.object], {}, [first, second]), ())
    context = view.get_context_data()
    assert context["protected_objects"] == [{"obj": first, "url": None}]
    assert context["related_objects"] == []
    assert context["delete_preview_truncated"] is True


def _objects(nodes):
    return [obj for node in nodes for obj in (node["obj"], *_objects(node["children"]))]


@pytest.mark.parametrize("limit", [1, 2, 3, 4, 5, 6, 50, None])
def test_delete_preview_selection_order(limit):
    from tests.test1.app.models import Book, Contract, Publisher

    root, child, last = Publisher(name="same"), Book(title="same"), Book(title="same")
    blocker = Contract(title="same")
    related = RelatedObjects([root, (child, [last]), [child]], {"book": 8}, [blocker, blocker])
    protected, nodes, truncated = DeleteView()._cv_select_delete_preview(related, limit)
    expected = [blocker, blocker, root, child, last, child]
    actual = [item["obj"] for item in protected] + _objects(nodes)
    assert actual == (expected if limit is None else expected[:limit])
    assert [id(obj) for obj in actual] == [id(obj) for obj in expected[: len(actual)]]
    assert truncated is (limit is not None and limit < len(expected))
    assert all(item["url"] is None and set(item) == {"obj", "url"} for item in protected)
    assert related.tree == [root, (child, [last]), [child]]
    assert related.summary == {"book": 8}


@pytest.mark.parametrize("limit", [1, 2, None])
@pytest.mark.parametrize("tail_visible", [False, True])
def test_delete_preview_selection_hidden(limit, tail_visible):
    from tests.test1.app.models import Book

    first, second = Book(title="First"), Book(title="Second")
    tree = [None, [None, (first, [None, [None, [second if tail_visible else None]]])]]
    related = RelatedObjects(tree, {}, [])
    protected, nodes, truncated = DeleteView()._cv_select_delete_preview(related, limit)
    expected = [first, second] if tail_visible else [first]
    assert protected == []
    assert _objects(nodes) == expected[:limit]
    assert nodes[0]["obj"] is first
    assert truncated is (tail_visible and limit == 1)
    assert related.tree == tree


@pytest.mark.parametrize("tree", [[], [None], [None, [None, (None, [None])]], [[None], (None,)]])
@pytest.mark.parametrize("limit", [1, None])
def test_delete_preview_selection_hidden_empty(tree, limit):
    assert DeleteView()._cv_select_delete_preview(RelatedObjects(tree, {}, []), limit) == ([], [], False)


@pytest.mark.parametrize("size", [0, 1, 49, 50, 51, 60])
@pytest.mark.parametrize("visible_root", [False, True])
def test_delete_preview_truncation_boundaries(size, visible_root):
    from tests.test1.app.models import Contract, Publisher

    root = Publisher(name="Root")
    blockers = [Contract(title=str(i)) for i in range(size)]
    related = RelatedObjects([root if visible_root else None, [None, [None]]], {}, blockers)
    protected, nodes, truncated = DeleteView()._cv_select_delete_preview(related, 50)
    assert len(protected) == min(size, 50)
    assert _objects(nodes) == ([root] if visible_root and size < 50 else [])
    assert truncated is (size + visible_root > 50)


@pytest.mark.django_db
@pytest.mark.parametrize("limit", [1, 3, None])
@pytest.mark.parametrize("link", [False, True])
def test_delete_preview_selection_occurrences(preview_view, monkeypatch, limit, link):
    from tests.test1.app.models import Book, Contract

    root = preview_view.object
    child, overflow = Book(title="Child"), Book(title="Overflow")
    blocker = Contract(title="Blocker")
    tree = [None, [root, [child, child, overflow]]]
    related = RelatedObjects(tree, {"redacted": 99}, [blocker])
    preview_view._cv_inspect_deletion = lambda: DeleteInspection(related, ())
    preview_view.cv_delete_preview_limit = limit
    preview_view.cv_link_related_objects = link
    calls = []

    def url(obj):
        assert obj is not blocker
        calls.append(obj)
        return f"/occurrence/{len(calls)}/"

    monkeypatch.setattr(Book, "__str__", lambda self: pytest.fail("Selection stringified a label"))
    monkeypatch.setattr(Contract, "__str__", lambda self: pytest.fail("Selection stringified a blocker"))
    preview_view.cv_get_related_object_url = url
    context = preview_view.get_context_data()
    selected = [root, child, child, overflow][: None if limit is None else limit - 1]
    assert calls == (selected if link else [])
    assert _objects(context["related_objects"]) == selected
    if link and limit is None:
        assert [node["url"] for node in context["related_objects"][0]["children"]] == [
            "/occurrence/2/",
            "/occurrence/3/",
            "/occurrence/4/",
        ]
    assert context["related_summary"] is related.summary
    assert related.tree == tree


@pytest.mark.django_db
def test_delete_preview_selection_isolation(preview_view):
    from tests.test1.app.models import Book

    items = [Book(pk=1, title="same"), Book(pk=1, title="same"), Book(pk=2, title="third")]
    related = RelatedObjects([None, items], {}, [])
    other = DeleteView()
    first = preview_view._cv_select_delete_preview(related, 1)
    unlimited = other._cv_select_delete_preview(related, None)
    assert _objects(first[1]) == items[:1]
    assert _objects(unlimited[1]) == items
    assert first == preview_view._cv_select_delete_preview(related, 1)
    assert unlimited == other._cv_select_delete_preview(related, None)
    assert [id(obj) for obj in related.tree[1]] == [id(obj) for obj in items]


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("limit", [1, None])
def test_delete_preview_selection_solo_root(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, publisher_penguin, monkeypatch, modal, limit
):
    from django.contrib.auth.models import Permission

    from tests.test1.app.views import PublisherCascadeDeleteView

    user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_publisher"))
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", modal)
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_delete_preview_limit", limit)
    response = client_user_publisher_cascade_delete.get(
        f"/publisher_cascade/{publisher_penguin.pk}/delete/", HTTP_X_CV_MODAL="true" if modal else "false"
    )
    assert response.status_code == 200
    assert response.context["related_summary"] == {}
    assert _objects(response.context["related_objects"]) == [publisher_penguin]
    content = response.content.decode()
    assert "Details about the related objects to be deleted:" in content
    assert "The following related objects will also be deleted:" not in content
    assert SHORTENED not in content


@pytest.mark.parametrize("summary", [{}, {"book": 120}])
@pytest.mark.parametrize("incomplete", [False, True])
@pytest.mark.parametrize("truncated", [False, True])
@pytest.mark.parametrize("nodes", [[], [{"obj": "Visible <row>", "url": None, "children": []}]])
def test_delete_preview_truncation_rendering(summary, incomplete, truncated, nodes):
    from django.template.loader import render_to_string

    content = render_to_string(
        "crud_views/view_delete.content.html",
        {
            "has_protected_objects": True,
            "protected_objects": [],
            "related_summary": summary,
            "related_summary_items": ["book: 120"] if summary else [],
            "related_objects": nodes,
            "delete_preview_incomplete": incomplete,
            "delete_preview_truncated": truncated,
        },
    )
    assert content.count(SHORTENED) == int(truncated)
    assert ("Details about the related objects to be deleted:" in content) is bool(nodes)
    assert ("This preview is incomplete." in content) is incomplete
    assert ("book: 120" in content) is bool(summary)
    assert "Other objects still reference this one" in content
    assert "<form" not in content
    if nodes:
        assert "Visible &lt;row&gt;" in content
    if truncated:
        assert content.index(SHORTENED) < content.index("Deletion is blocked")


def test_delete_preview_limit_precedence_default():
    assert getattr(CrudViewsSettings(), "delete_preview_limit", "missing") == 50


@pytest.mark.parametrize("project", [None, 1, 50])
@pytest.mark.parametrize("override", ["unset", None, 3])
def test_delete_preview_limit_precedence(monkeypatch, project, override):
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", project)

    class Base(DeleteView):
        pass

    if override != "unset":
        Base.cv_delete_preview_limit = override

    class Inherited(Base):
        pass

    for view in (Base, Inherited):
        assert view()._cv_get_delete_preview_limit() == (project if override == "unset" else override)
        assert "viewset.E265" not in {message.id for check in view.checks() for message in check.messages()}


@pytest.mark.parametrize("value", [True, False, 1.5, "2", 0, -1, [], {}, object()])
def test_delete_preview_limit_invalid(monkeypatch, value):
    configured = CrudViewsSettings(delete_preview_limit=value)
    assert any(message.id == "crud_views.E109" for message in configured.check_messages)
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", value)
    with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
        DeleteView()._cv_get_delete_preview_limit()

    class Invalid(DeleteView):
        cv_delete_preview_limit = value

    assert "viewset.E265" in {message.id for check in Invalid.checks() for message in check.messages()}
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", 50)
    with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
        Invalid()._cv_get_delete_preview_limit()


@pytest.mark.django_db
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize(
    "project,override,valid", [(False, "unset", False), (50, False, False), (False, 2, True), (False, None, True)]
)
def test_delete_preview_limit_invalid_request(
    client_user_publisher_delete, publisher_penguin, monkeypatch, settings, preview, project, override, valid
):
    from tests.test1.app.views import PublisherDeleteView

    settings.CRUD_VIEWS_STRICT_CHECKS = False
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", project)
    monkeypatch.setattr(PublisherDeleteView, "cv_show_related_objects", preview)
    if override != "unset":
        monkeypatch.setattr(PublisherDeleteView, "cv_delete_preview_limit", override)
    assert any(m.id == "crud_views.E109" for m in crud_views_settings.check_messages) is (project is False)
    path = f"/publisher/{publisher_penguin.pk}/delete/"
    if valid:
        assert client_user_publisher_delete.get(path).status_code == 200
    else:
        with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
            client_user_publisher_delete.get(path)
