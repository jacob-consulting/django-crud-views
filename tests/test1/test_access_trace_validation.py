"""Adversarial regressions found while validating phase 06.34."""

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
