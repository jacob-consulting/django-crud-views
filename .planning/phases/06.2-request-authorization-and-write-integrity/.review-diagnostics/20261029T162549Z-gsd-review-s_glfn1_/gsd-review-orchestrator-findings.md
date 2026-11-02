# Orchestrator verification supplement

## ORCH-01 — HIGH: plan 08 catches lifecycle errors after deletion may already have committed

Plan `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-08-PLAN.md:135` specifies catching `ProtectedError` and `RestrictedError` around the whole `cv_form_valid_process(context)` call, then returning a blocked response. Its justification says both exceptions come from the collector before delete SQL and that `transaction.on_commit` was never scheduled.

That is true for an exception raised by the target object's initial collector, but not for every exception crossing this boundary. `src/crud_views/lib/views/mixins.py:54` runs the delete, `cv_form_valid_hook`, and callback registration in the same method; leaving its outer atomic block can execute `cv_on_commit` before the method returns. `src/crud_views/lib/view/base.py:244` also supports `cv_atomic=False`. A user callback can attempt deletion of an unrelated protected object and raise either exception after the original target's deletion has committed. Existing real-commit semantics are independently pinned by `tests/test1/test_transactions.py:619`.

The temporary probe below used the unchanged `PublisherDeleteView.cv_form_valid_process` and in-memory test database. It disabled only the normal success-message hook (a direct view instance has no request), raised each exception from `cv_on_commit`, and placed the proposed catch around the call. All four cases reached that catch with the Publisher already absent, on both cached environments:

- Django 6.0: **4 passed in 0.36s**.
- Django 4.2: **4 passed in 0.40s**.

These passes demonstrate the counterexample, not successful implementation of plan 08. The current production `post()` was not changed; the probe verifies the exception boundary rather than asserting a future rendered HTTP response. An initial probe failed because the direct view had no request for its success-message hook; that setup error was corrected before these results.

**Required plan improvement:** scope or tag protection failures from the target deletion before treating them as blocked responses. Preserve propagation of failures from lifecycle hooks and commit callbacks. Add real-commit regressions for both exception types, with atomic writes on and off, proving that a completed deletion is never reported as prevented. Preserve the existing pre-write PROTECT/RESTRICT response and rollback tests. The final design must not assume every exception of these two classes came from the target collector.

This is an orchestrator-confirmed finding, not a third external-reviewer vote. Fable and Gemini affirm the broad backstop for collector-origin errors but do not examine this callback-origin counterexample.

## Reproduction

Run from the repository root with the probe saved as a temporary Python file:

```bash
PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest -p tests.test1.conftest /path/to/test_review_backstop.py -q -p no:cacheprovider
```

```python
import pytest
from django.db.models import ProtectedError, RestrictedError
from tests.test1.app.models import Publisher
from tests.test1.app.views import PublisherDeleteView

@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('error_type', [ProtectedError, RestrictedError])
@pytest.mark.parametrize('atomic', [True, False])
def test_proposed_catch_can_run_after_delete_commit(monkeypatch, error_type, atomic):
    publisher = Publisher.objects.create(name='Review callback probe')
    original_pk = publisher.pk
    view = PublisherDeleteView()
    view.object = publisher
    view.cv_atomic = atomic
    monkeypatch.setattr(view, 'cv_form_valid_hook', lambda context: None)
    def callback(context):
        raise error_type('Callback encountered unrelated protected relationship', set())
    monkeypatch.setattr(view, 'cv_on_commit', callback)
    caught_as_blocked = False
    try:
        view.cv_form_valid_process({})
    except (ProtectedError, RestrictedError):
        caught_as_blocked = True
    assert caught_as_blocked
    assert not Publisher.objects.filter(pk=original_pk).exists()
```
