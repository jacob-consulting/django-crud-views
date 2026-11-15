"""Adversarial regressions found while validating phase 06.34."""

import json

import pytest

from tests.test1 import test_access_trace_command as command_tests

process_env = command_tests.process_env
run_process = command_tests.run_process


@pytest.mark.parametrize("as_json", [False, True], ids=["text", "json"])
def test_malformed_full_url_keeps_command_error_exit_code(process_env, as_json):
    """A malformed URL is a wrong call/error, never an authorization denial."""
    args = ["http://[", "--anonymous", *(["--as-json"] if as_json else [])]

    result = run_process(process_env, *args)

    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    if as_json:
        data = json.loads(result.stdout)
        assert data["outcome"] == "error"
        assert data["steps"][data["decided_by"] - 1]["exception"]["class"] == "ValueError"


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["http://[", "http://example.com\uff0fwrong/"])
def test_malformed_url_is_a_shared_trace_error_without_database_work(path, django_assert_num_queries):
    from crud_views.lib.access_trace import trace_access

    with django_assert_num_queries(0):
        trace = trace_access(path, None)
    assert trace.path == path and trace.outcome == "error"
    assert trace.route is None and trace.plan == []
    assert trace.steps[trace.decided_by - 1].exception["class"] == "ValueError"


@pytest.mark.django_db
def test_german_guardian_command_translates_its_explanatory_message(cv_guardian_author, django_user_model):
    """Guardian prose reaches the same translated output boundary as core prose."""
    from django.urls import reverse
    from django.utils import translation
    from guardian.shortcuts import assign_perm

    from tests.test1.test_access_trace_command import invoke

    actor = django_user_model.objects.create_user(username="german diagnostic actor")
    obj = cv_guardian_author.model.objects.create(first_name="private", last_name="contents")
    assign_perm(cv_guardian_author.permissions["view"], actor, obj)
    path = reverse(cv_guardian_author.get_router_name("detail"), kwargs={cv_guardian_author.pk_name: obj.pk})

    with translation.override("en"):
        english_code, english, english_error = invoke(path, actor.username, "--no-color")
    with translation.override("de"):
        german_code, german, german_error = invoke(path, actor.username, "--no-color")

    assert english_code == german_code == 0
    assert english_error == german_error == ""
    assert "model fallback enabled: False" in english
    assert "Schritte:" in german
    assert "model fallback enabled:" not in german, "Guardian's explanatory prose remains English in German output"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["detail", "list", "create"])
@pytest.mark.parametrize("actor_kind", ["anonymous", "inactive", "active"])
def test_guardian_message_family_is_localized_in_real_json(kind, actor_kind):
    from django.utils import translation

    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
    from tests.test1.app.models import Book, Publisher
    from tests.test1.test_access_trace_command import invoke
    from tests.test1.test_access_trace_guardian import local_routes, nested_routes
    from tests.test1.test_access_trace_locales import stable
    from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes

    actor = _user("translated", superuser=True)
    if actor_kind == "inactive":
        actor.is_active = False
        actor.save()
    selector = ["--anonymous"] if actor_kind == "anonymous" else [actor.username]
    pub = Publisher.objects.create(name="private contents")
    book = Book.objects.create(title="private contents", publisher=pub)
    base = GuardianDetailViewPermissionRequired if kind == "detail" else GuardianListViewPermissionRequired
    build = nested_routes if kind == "create" else lambda suffix: local_routes(suffix, base=base)
    with isolated_routes(build) as routes:
        if kind == "create":
            outer, inner, leaf, _, key = routes
            path = _url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk})
        else:
            vs, _ = routes
            path = _url(vs, "tested", **({"pk": pub.pk} if kind == "detail" else {}))
        results = {}
        for language in ("en", "de"):
            with translation.override(language):
                code, output, error = invoke(path, *selector, "--as-json", "--no-color")
            assert code == {"active": 0, "inactive": 1, "anonymous": 1}[actor_kind] and error == ""
            results[language] = json.loads(output)
        assert stable(results["en"]) == stable(results["de"])
        english = [s["message"] for s in results["en"]["steps"] if s["provider"] == "guardian" and s["message"]]
        german = [s["message"] for s in results["de"]["steps"] if s["provider"] == "guardian" and s["message"]]
        assert english and len(english) == len(german)
        assert all(en != de for en, de in zip(english, german, strict=True))
        assert not any(
            phrase in message
            for message in german
            for phrase in ("anonymous policy:", "inactive actor", "queryset filter", "model fallback enabled:")
        )
