import nox

DJANGO_VERSIONS = ["4.2", "5.2", "6.0"]


@nox.session(python=["3.12", "3.13", "3.14", "3.15"], venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session, django):
    # Django 4.2 does not support Python 3.14+
    if django == "4.2" and session.python in ("3.14", "3.15"):
        session.skip(f"Django 4.2 does not support Python {session.python}")

    session.install(f"django~={django}.0")
    session.install(".[polymorphic,workflow,ordered,test]")

    # One XML report per session: all sessions run from the repo root, so a shared
    # coverage.xml would be overwritten by each session in turn. See issue #105.
    xml_report = f"--cov-report=xml:coverage-py{session.python}-dj{django}.xml"
    session.run("pytest", "tests", "-n", "auto", "--cov", "--cov-report=term-missing", xml_report, *session.posargs)


# The declared floors in pyproject.toml ("django-crispy-forms (>=2.0)", "crispy-bootstrap5 (>=2023.10)"). The pins are
# installed in the same resolver transaction as the project and its extras, so nothing can upgrade them.
CRISPY_FLOOR = {"django-crispy-forms": "2.0", "crispy-bootstrap5": "2023.10"}

# The form-button leaf feature suite (Phase 06): crispy adapters and goldens, the normalizer, host icons, the filter
# helper, owner/config resolution, system checks, workflow forms, CRUD pages, modals and cancel origins.
CRISPY_FLOOR_TESTS = [
    "tests/test1/test_crispy_buttons.py",
    "tests/test1/test_form_buttons_golden.py",
    "tests/test1/test_button_data.py",
    "tests/test1/test_icon_host_leaves.py",
    "tests/test1/test_icons_registry.py",
    "tests/test1/test_filter.py",
    "tests/test1/test_filter_pinned.py",
    "tests/test1/test_filter_toggle_label_mode.py",
    "tests/test1/test_action_label_mode_config.py",
    "tests/test1/test_label_mode.py",
    "tests/test1/test_label_mode_docs.py",
    "tests/test1/test_button_classes_templates.py",
    "tests/test1/test_form_button_checks.py",
    "tests/test1/test_settings_checks.py",
    "tests/test1/test_button_classes_checks.py",
    "tests/test1/test_icons_checks.py",
    "tests/test1/test_workflow.py",
    "tests/test1/test_crud.py",
    "tests/test1/test_delete.py",
    "tests/test1/test_custom_form_view.py",
    "tests/test1/test_form_frame.py",
    "tests/test1/test_modal.py",
    "tests/test1/test_cancel_origin.py",
]

# The filter region golden is byte-exact over the template pack's own wrapper markup (field label, FormActions
# <div>), whose whitespace changed after crispy-bootstrap5 2023.10. At the floor the leaf-owned controls are proven
# byte for byte by test_filter_form_controls_match_golden instead; nothing else is deselected.
CRISPY_FLOOR_DESELECT = ["--deselect", "tests/test1/test_form_buttons_golden.py::test_filter_form_baseline"]

# Runs inside the session venv: prints the resolved versions and fails unless the floor pins and the requested Django
# series are what is actually installed (metadata alone proves nothing, so the suite runs afterwards).
_FLOOR_VERSIONS = """
import importlib.metadata as metadata, json, platform, sys

expected, django_series = json.loads(sys.argv[1]), sys.argv[2]
names = ["django", *expected, "django-filter", "django-tables2", "django-fsm-2", "django-polymorphic"]
found = {name: metadata.version(name) for name in names}
print(f"crispy_floor: python {platform.python_version()}; " + "; ".join(f"{n} {v}" for n, v in found.items()))
errors = [f"{n} {found[n]} != {v}" for n, v in expected.items() if found[n] != v]
if not (found["django"] == django_series or found["django"].startswith(django_series + ".")):
    errors.append(f"django {found['django']} is not the {django_series} series")
if errors:
    sys.exit("crispy_floor: " + "; ".join(errors))
"""

# Django 6.0 removed format_html() without arguments: every call in the package must pass at least one argument, and
# the one-argument form must still escape on the installed Django.
_FORMAT_HTML_AUDIT = """
import ast, pathlib, sys
from django.utils.html import format_html

assert format_html('<i class="{}"></i>', '"x<&') == '<i class="&quot;x&lt;&amp;"></i>'
calls = bad = 0
for path in sorted(pathlib.Path("src").rglob("*.py")):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        func = getattr(node, "func", None)
        if isinstance(node, ast.Call) and getattr(func, "id", getattr(func, "attr", None)) == "format_html":
            calls += 1
            if len(node.args) + len(node.keywords) < 2:
                bad += 1
                print(f"{path}:{node.lineno}: format_html() without arguments")
print(f"crispy_floor: {calls} format_html call(s) in src, all with arguments" if not bad else "")
sys.exit(1 if bad else 0)
"""


@nox.session(python=["3.12"], venv_backend="uv")
@nox.parametrize("django", ["4.2", "6.0"])
def crispy_floor(session, django):
    """The form-button leaf feature suite at the declared crispy floors, on the oldest and newest Django series."""
    import json

    pins = [f"{name}=={version}" for name, version in CRISPY_FLOOR.items()]
    session.install(f"django~={django}.0", ".[polymorphic,workflow,ordered,test]", *pins)
    session.run("python", "-I", "-c", _FLOOR_VERSIONS, json.dumps(CRISPY_FLOOR), django)
    session.run("python", "-I", "-c", _FORMAT_HTML_AUDIT)
    session.run("pytest", *CRISPY_FLOOR_TESTS, *CRISPY_FLOOR_DESELECT, "-n", "auto", *session.posargs)


@nox.session(python=["3.12", "3.13", "3.14", "3.15"], venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def examples(session, django):
    # Django 4.2 does not support Python 3.14+
    if django == "4.2" and session.python in ("3.14", "3.15"):
        session.skip(f"Django 4.2 does not support Python {session.python}")

    session.install(f"django~={django}.0")
    session.install(".[all,test,examples]", "-r", "requirements/demo.txt")

    with session.chdir("./examples/bootstrap5"):
        session.run("pytest", *session.posargs)
