from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_workflow_app_has_no_missing_migrations():
    """`makemigrations --check` must be clean for the cvw app.

    Regression: the WorkflowInfo Meta index had no explicit name, so Django auto-generated a
    hashed name that differed from the name shipped in migration 0002, making `makemigrations`
    perpetually propose a RenameIndex for consumers.
    """
    out = StringIO()
    call_command("makemigrations", "cvw", dry_run=True, stdout=out, stderr=out)
    assert "No changes detected" in out.getvalue(), f"cvw has missing migrations:\n{out.getvalue()}"
