# Cycle 3 supplementary runtime probes

Both probes ran read-only in separate local processes; no source/configuration files were changed and no full baseline suite was rerun.

## A22: Django 4.2 proposed delete override

Interpreter: `.nox/crispy_floor-3-12-django-4-2/bin/python`.
Subclass `django.views.generic.edit.DeleteView`, defining only `delete()` that delegates to `http_method_not_allowed`; instantiate under `warnings.catch_warnings(record=True)` with `simplefilter("always")`.

Observed: one `DeleteViewCustomDeleteWarning`: "DeleteView uses FormMixin to handle POST requests. As a consequence, any custom deletion logic in PlannedDeleteView.delete() handler should be moved to form_valid()."
Exit: 0.

## A23: actual Guardian mixin MRO

Interpreter: `.nox/crispy_floor-3-12-django-6-0/bin/python`, PYTHONPATH pointing at repository/src and repository; initialize existing test Django settings.
Define `CustomObjectMixin(GuardianObjectPermissionMixin)` with global fallback True and anonymous mode '404', then `Composed(GuardianParentPermissionMixin, CustomObjectMixin)`.

Observed current: `True 404`.
After assigning the proposed False/'redirect' values to GuardianParentPermissionMixin in the subprocess: `False redirect`.
After removing those values and defining annotation-only declarations: `True 404`.
Exit: 0. Process exit discards these in-memory class mutations.
