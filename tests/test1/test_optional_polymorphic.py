"""Covers the django-polymorphic import guard in lib/formsets/render_tree.py.

`polymorphic` is a genuinely optional dependency (the `polymorphic` extra), so
`render_tree` must import cleanly without it. Mirrors test_optional_ordered.py,
which does the same for django-ordered-model. See issue #107.
"""

import importlib
import sys


def test_render_tree_exposes_polymorphic_base_when_installed():
    """With django-polymorphic installed, the real class is bound."""
    from crud_views.lib.formsets import render_tree

    assert render_tree.BasePolymorphicInlineFormSet is not None


def test_render_tree_imports_without_polymorphic(monkeypatch):
    """render_tree must import cleanly when django-polymorphic is absent."""
    from crud_views.lib.formsets import formsets as formsets_mod
    from crud_views.lib.formsets import render_tree

    # Snapshot both modules' namespaces before mutating anything. render_tree
    # defines XForm and XFormSet as mutually forward-referencing pydantic
    # models (each names the other before it is defined, resolved lazily via
    # `from __future__ import annotations`); formsets.py did
    # `from .render_tree import XForm, XFormSet` at its own import time, so
    # both modules must agree on one set of class objects.
    #
    # A second `importlib.reload` would not restore that agreement: pydantic
    # resolves XForm's forward reference to "XFormSet" against whatever the
    # module dict holds *at that moment* mid-exec, which — on a *second*
    # reload — is still the previous (hidden-polymorphic) generation, since
    # the new XFormSet class statement hasn't run yet. The result is a
    # `XForm` class permanently bound to the *wrong* `XFormSet` generation,
    # which later raises `pydantic_core.ValidationError` for unrelated
    # formset tests (e.g. test_formsets_validation_gate.py) whenever they
    # run in the same process after this one. Restoring by replaying the
    # original namespace snapshot sidesteps that reload-ordering hazard
    # entirely: no new class generation is ever created for the restore.
    render_tree_snapshot = vars(render_tree).copy()
    formsets_snapshot = vars(formsets_mod).copy()

    try:
        # Hide polymorphic and the submodule the guard actually imports from.
        monkeypatch.setitem(sys.modules, "polymorphic", None)
        monkeypatch.setitem(sys.modules, "polymorphic.formsets", None)

        reloaded = importlib.reload(render_tree)
        assert reloaded.BasePolymorphicInlineFormSet is None
    finally:
        # Always restore, even if the reload or the assertion above raised —
        # otherwise render_tree is left holding the hidden-polymorphic class
        # generation for the rest of this worker process, and every later
        # formset test in it fails with a confusing pydantic ValidationError
        # that buries the real cause.
        monkeypatch.undo()

        vars(render_tree).clear()
        vars(render_tree).update(render_tree_snapshot)
        vars(formsets_mod).clear()
        vars(formsets_mod).update(formsets_snapshot)

    assert render_tree.XForm is render_tree_snapshot["XForm"]
    assert render_tree.XFormSet is render_tree_snapshot["XFormSet"]
    assert render_tree.BasePolymorphicInlineFormSet is not None
