"""Compiled German diagnostics at real trace, command and inherited-page boundaries."""

import json

import pytest
from django.core.management.base import CommandError
from django.utils import translation
from django.utils.translation import trans_real
from lxml import html

from crud_views.lib.access_trace import trace_access
from tests.test1 import test_manage_access_trace as web
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace_command import invoke
from tests.test1.test_ancestor_authorization import _url, isolated_routes
from tests.test1.test_manage_requirements import grant, register

developer = web.developer
enabled = web.enabled
host = web.host
submit = web.submit

pytestmark = pytest.mark.django_db

NOTICES = {
    "en": "other middleware and URL decorators are not traced",
    "de": "Andere Middleware und URL-Dekoratoren werden nicht nachverfolgt",
}


@pytest.fixture(autouse=True)
def fresh_catalog(monkeypatch):
    monkeypatch.setattr(trans_real, "_translations", {})


def stable(value):
    """Retain every schema key, machine code and fact; replace only localized prose."""
    if isinstance(value, dict):
        return {key: None if key in {"message", "untraced"} else stable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def test_notices_are_assembled_once_and_reach_every_real_output(client, host, developer, enabled):
    path = "/author/manage/"
    documents = {}
    for language, notice in NOTICES.items():
        with translation.override(language):
            trace = trace_access(path, developer)
            data = trace.to_dict()
            assert notice in data["untraced"]
            code, stdout, stderr = invoke(path, developer.username, "--as-json", "--no-color")
            assert code == 0 and stderr == ""
            parsed = json.loads(stdout)
            assert notice in parsed["untraced"]
            assert parsed == data
            code, stdout, stderr = invoke(path, developer.username, "--no-color")
            assert code == 0 and stderr == "" and notice in stdout
            response = submit(
                client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path=path
            )
            assert response.status_code == 200
            card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
            assert notice in card.text_content()
            assert response.context["manage_access_trace"]["trace"] == data
            documents[language] = data
        with translation.override("de" if language == "en" else "en"):
            assert trace.to_dict() == data
    assert stable(documents["en"]) == stable(documents["de"])


@pytest.mark.parametrize("empty_matrix", [False, True])
@pytest.mark.parametrize("state", ["default", "unknown", "path", "other", "self"])
def test_compiled_actor_wording_in_both_matrix_layouts(
    client, host, developer, enabled, django_user_model, monkeypatch, empty_matrix, state
):
    from crud_views.lib.viewset import ViewSet

    other = django_user_model.objects.create_user(username="geprüfter Benutzer")
    if empty_matrix:
        monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {}))
    selected = other if state == "other" else developer
    params = {"cv_access_mode": "viewset", "cv_access_user": selected.username}
    if state == "default":
        params = {}
    elif state == "unknown":
        params["cv_access_user"] = "unbekannt"
    elif state == "path":
        params.update(cv_access_mode="path", cv_access_path="/author/manage/")
    with translation.override("de"):
        response = submit(client, host, developer, **params)
    assert response.status_code == 200
    matrix = response.context["manage_permissions"]
    checked = state in {"other", "self"}
    assert matrix["actor"]["id"] == (selected.pk if checked else developer.pk)
    label = html.fromstring(response.content).cssselect("[data-manage-actor]")[0].text_content()
    expected = (
        f"Zugriff für: {selected.username} (unten geprüft)" if checked else f"Zugriff für: {developer.username} (Sie)"
    )
    assert expected in label
    assert ("(Sie)" in label) is not checked
    assert response.wsgi_request.user.pk == developer.pk


@pytest.mark.parametrize("mode", ["viewset", "path"])
@pytest.mark.parametrize("selector", ["username", "pk", "collision", "unknown"])
def test_compiled_forms_keep_selector_semantics(client, host, developer, enabled, django_user_model, mode, selector):
    actor = django_user_model.objects.create_user(username="<script>ausgewählt</script>")
    identifier = actor.username if selector == "username" else str(actor.pk)
    if selector == "collision":
        actor = django_user_model.objects.create_user(username=identifier)
    elif selector == "unknown":
        identifier = "<script>unbekannt</script>"
    with translation.override("de"):
        response = submit(
            client, host, developer, cv_access_mode=mode, cv_access_user=identifier, cv_access_path="/author/manage/"
        )
    assert response.status_code == 200
    document = html.fromstring(response.content)
    card = document.cssselect("#cv-manage-access-trace")[0]
    text = card.text_content()
    assert card.cssselect("h2")[0].text_content() == "Zugriffsprüfung"
    assert [node.text_content() for node in card.cssselect("legend")] == ["Dieses ViewSet", "Beliebige URL"]
    assert [node.text_content() for node in card.cssselect('button[type="submit"]')] == ["Prüfen", "Prüfen"]
    assert sum(node.text_content() == "Benutzername oder Primärschlüssel" for node in card.cssselect("label")) == 2
    assert "Objekt-Primärschlüssel (optional)" in text
    assert card.cssselect("a[data-cv-manage-help]")[0].get("aria-label") == "Dokumentation: Zugriffsprüfung"
    assert "<script>" not in response.content.decode()
    data = response.context["manage_access_trace"]
    if selector == "unknown":
        assert data["error"] == "Unbekannter Benutzer: <script>unbekannt</script>"
        assert data["trace"] is None and data["rows"] == []
        assert "&lt;script&gt;unbekannt&lt;/script&gt;" in response.content.decode()
    else:
        assert data["actor"]["pk"] == str(actor.pk)
        assert f"Zugriffsprüfung für: {actor.username}" in text
        if mode == "viewset":
            assert response.context["manage_permissions"]["actor"]["id"] == actor.pk
            assert [row["key"] for row in data["rows"]] == list(host.get_all_views())
        else:
            assert data["trace"]["user"]["pk"] == str(actor.pk)


@pytest.mark.parametrize(
    "object_pk,expected", [("", "benötigt einen Objekt-Primärschlüssel"), ("not-a-uuid", "verwenden Sie das Pfadfeld")]
)
def test_compiled_pk_instructions(client, host, developer, enabled, object_pk, expected):
    with translation.override("de"):
        response = submit(
            client, host, developer, cv_access_mode="viewset", cv_access_user=developer.username, cv_access_pk=object_pk
        )
    rows = {row["key"]: row for row in response.context["manage_access_trace"]["rows"]}
    for key in ("detail", "update", "delete"):
        assert rows[key]["instruction"] == expected and rows[key]["trace"] is None
        node = html.fromstring(response.content).cssselect(f'[data-cv-access-row="{key}"]')[0]
        assert expected in node.text_content()


OUTCOMES = {
    "allowed": (0, "Erlaubt"),
    "denied": (1, "Verweigert"),
    "not_found": (1, "Nicht gefunden"),
    "login_redirect": (1, "Weiterleitung zur Anmeldung"),
    "error": (2, "Fehler"),
    "no_such_route": (2, "Keine solche Route"),
}


@pytest.mark.parametrize("outcome", OUTCOMES)
def test_real_translated_outcomes_preserve_facts_and_escape_errors(
    client, host, developer, enabled, django_user_model, outcome
):
    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views.lib.viewset import ViewSet

    payload = "<script>Fehler & geheim</script>"

    def broken_gate(self):
        raise ValueError(payload)

    def build(suffix):
        vs = ViewSet(model=Publisher, name="localeoutcome" + suffix)
        register(DetailViewPermissionRequired, vs, **({"has_permission": broken_gate} if outcome == "error" else {}))
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="object content must not appear")
        actor = django_user_model.objects.create_user(username="Ergebnisbenutzer")
        if outcome in {"allowed", "not_found"}:
            grant(actor, vs, "view")
        path = (
            "/missing/"
            if outcome == "no_such_route"
            else _url(vs, "tested", pk=99999 if outcome == "not_found" else obj.pk)
        )
        selector = ["--anonymous"] if outcome == "login_redirect" else [actor.username]
        with translation.override("en"):
            english = trace_access(path, None if outcome == "login_redirect" else actor).to_dict()
        with translation.override("de"):
            code, stdout, stderr = invoke(path, *selector, "--as-json", "--no-color")
            data = json.loads(stdout)
            assert code == OUTCOMES[outcome][0] and stderr == ""
            assert data["outcome"] == outcome
            assert stable(data) == stable(english)
            assert NOTICES["de"] in data["untraced"]
            code, text, err = invoke(path, *selector, "--no-color")
            assert code == OUTCOMES[outcome][0]
            if outcome == "no_such_route":
                assert text == "" and err == f"Keine solche CRUD-View-Route: {path}\n"
            else:
                assert OUTCOMES[outcome][1] in text and err == ""
                assert "Pfad:" in text and "Schritte:" in text and NOTICES["de"] in text
            # Web intentionally offers no anonymous selector; other outcomes use the same real path.
            if outcome != "login_redirect":
                response = submit(
                    client, host, developer, cv_access_mode="path", cv_access_user=actor.username, cv_access_path=path
                )
                assert response.status_code == 200
                card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
                assert OUTCOMES[outcome][1] in card.text_content()
                assert response.context["manage_access_trace"]["trace"] == data
                if data["decided_by"] is not None:
                    assert f"entschieden bei Schritt {data['decided_by']}" in card.text_content()
                if outcome == "error":
                    assert payload in card.text_content() and payload not in response.content.decode()
                    assert "&lt;script&gt;Fehler &amp; geheim&lt;/script&gt;" in response.content.decode()
                if outcome == "denied":
                    assert "Nicht erreicht" in card.text_content()
                    assert any(step["result"] == "not_reached" for step in data["steps"])
            if outcome in {"allowed", "denied"}:
                assert any(step["permission"] == vs.permissions["view"] for step in data["steps"])
            assert "object content must not appear" not in stdout


def test_compiled_command_help_and_unknown_user():
    from crud_views.management.commands.cv_access import Command

    with translation.override("de"):
        help_text = Command().create_parser("manage.py", "cv_access").format_help()
        assert "Benutzername oder Primärschlüssel" in help_text
        assert "Projektpfad oder vollständige URL" in help_text
        with pytest.raises(CommandError, match="Unbekannter Benutzer: niemand"):
            invoke("/author/", "niemand")


@pytest.mark.parametrize("count", [0, 1, 3])
def test_compiled_plural_resource_counts_from_real_loader(client, host, developer, enabled, count):
    from crud_views.lib.resource import Resource, ResourceViewMixin
    from crud_views.lib.views import ListView
    from crud_views.lib.viewset import ViewSet

    class Row(Resource):
        key: str

        class Meta:
            pk_field = "key"

        @classmethod
        def cv_get_items(cls, request, **kwargs):
            return [cls(key=str(index)) for index in range(count)]

    def build(suffix):
        vs = ViewSet(model=Row, name="localerows" + suffix)
        register(type("Rows", (ResourceViewMixin, ListView), {"__module__": __name__}), vs)
        return vs, [vs]

    with isolated_routes(build) as vs, translation.override("de"):
        path = _url(vs, "tested")
        data = trace_access(path, developer).to_dict()
        assert data["outcome"] == "allowed"
        assert [step["counts"] for step in data["steps"] if step["kind"] == "list_filter"] == [
            {"visible": count, "total": None}
        ]
        expected = "1 Zeile" if count == 1 else f"{count} Zeilen"
        code, stdout, _ = invoke(path, developer.username, "--no-color")
        assert code == 0 and expected in stdout
        response = submit(
            client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path=path
        )
        assert expected in html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()


@pytest.mark.parametrize("count", [0, 1, 3])
def test_compiled_guardian_counts_and_handler_limitations(client, host, developer, enabled, cv_guardian_author, count):
    from django.urls import reverse
    from guardian.shortcuts import assign_perm

    for index in range(count):
        obj = cv_guardian_author.model.objects.create(first_name="private", last_name=str(index))
        assign_perm(cv_guardian_author.permissions["view"], developer, obj)
    cv_guardian_author.model.objects.create(first_name="invisible", last_name="private")
    with translation.override("de"):
        path = reverse(cv_guardian_author.get_router_name("list"))
        code, stdout, _ = invoke(path, developer.username, "--no-color")
        assert code == 0 and f"sieht {count} von {count + 1} Objekten" in stdout
        response = submit(
            client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path=path
        )
        assert (
            f"sieht {count} von {count + 1} Objekten"
            in html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()
        )
        obj = host.model.objects.create(first_name="private", last_name="deleted")
        path = reverse(host.get_router_name("delete"), kwargs={host.pk_name: obj.pk})
        response = submit(
            client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path=path
        )
        card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
        assert "Nicht ausgewertet" in card.text_content()
        assert "Die Konfiguration der Löschvorschau wird beim Aufbau der Seite geprüft." in card.text_content()
        trace = response.context["manage_access_trace"]["trace"]
        assert any(step["key"] == "delete_preview" and step["result"] == "not_evaluated" for step in trace["steps"])
