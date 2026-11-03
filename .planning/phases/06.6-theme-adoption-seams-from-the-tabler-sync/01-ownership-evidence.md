# Plan 01 ownership evidence

Pinned baseline: `cb26af4dfef2afb31d774a219abfad1c675cdff1`, unpacked using git archive in an independent task-owned temporary directory.
Execution HEAD: `66f2e01abd1b29924a30cb8191b4143a5b338d5a`; initial tracked dirty src diff SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty source diff).

## Unchanged baseline

Command from archive: `PYTHONPATH=src:. <checkout>/.nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_form_frame.py tests/test1/test_form_button_checks.py tests/test1/test_crispy_buttons.py -n 4 -q`.

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  7%]
........................................................................ [ 15%]
........................................................................ [ 23%]
........................................................................ [ 31%]
........................................................................ [ 39%]
........................................................................ [ 47%]
........................................................................ [ 55%]
........................................................................ [ 63%]
........................................................................ [ 71%]
........................................................................ [ 78%]
........................................................................ [ 86%]
........................................................................ [ 94%]
................................................                         [100%]
912 passed in 11.57s
```

Setup correction: first archive launcher used unavailable `python`; reran using `python3` before capturing this archive baseline. The first incidental checkout run also passed 912 tests in 10.78s, but is not the pinned baseline. Probe import corrected from nonexistent app.forms to app.views before experiments.

## Bounded helper experiment

No Context7 tool or ctx7 CLI available. Consulted official crispy helper docs and inspected installed helper.py/crispy_forms_tags.py. Sources: https://django-crispy-forms.readthedocs.io/en/2.5/crispy_tag_forms.html and https://django-crispy-forms.readthedocs.io/en/2.0/_modules/helper.html .

Compared shallow copy with a FormHelper-compatible forwarding adapter. Adapter delegates layout/get_attributes hooks to the original helper, makes a fresh attribute mapping and sets only that mapping's disable_csrf=True. Original helper/layout are never assigned. A shallow copy cannot cover aliases, raising copy hooks, or read-only suppression properties. Adapter uses the dependency's get_attributes seam, avoids copy entirely, preserves shared layout identity and hooks. Thus A2 is resolved through the render adapter rather than a universal copy assumption.

### Current cached runtime and actual output

```json
{
  "python": "/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python",
  "versions": {
    "Django": "5.2.18",
    "django-crispy-forms": "2.7",
    "crispy-bootstrap5": "2026.9"
  },
  "helper_module": "/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/crispy_forms/helper.py",
  "experiments": [
    {
      "helper": "FormHelper",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Aliasing",
      "copy": "alias: refused to mutate",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Raising",
      "copy": "RuntimeError: copy forbidden",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "ReadOnly",
      "copy": "AttributeError: property 'disable_csrf' of 'ReadOnly' object has no setter",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Hooks",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    }
  ],
  "raw_create": "\n<form class=\"cv-form\" method=\"post\" action=\"/\" enctype=\"multipart/form-data\" novalidate>\n    <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"SRrrJIp1MYfLspPB1vbWJc8CDg2jPy5q8pdy3GkLTMoWZPDMbQuzf7yCtk0pN2lw\">\n\n    \n\n    \n\n\n    \n\n<form  method=\"post\" > <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"SRrrJIp1MYfLspPB1vbWJc8CDg2jPy5q8pdy3GkLTMoWZPDMbQuzf7yCtk0pN2lw\"> <div id=\"div_id_name\" class=\"mb-3\"> <label\n                for=\"id_name\" class=\"form-label requiredField\">\n                Name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"name\" class=\"textinput form-control\" required id=\"id_name\"> </div> </form>\n\n\n\n</form>\n\n",
  "raw_standalone_model_form": "\n\n<form  method=\"post\" > <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"test-token\"> <div  class=\"row \" > <div \n     class=\"col-md-4\" > <div id=\"div_id_first_name\" class=\"mb-3\"> <label\n                for=\"id_first_name\" class=\"form-label requiredField\">\n                First name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"first_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_first_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_last_name\" class=\"mb-3\"> <label\n                for=\"id_last_name\" class=\"form-label requiredField\">\n                Last name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"last_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_last_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_pseudonym\" class=\"mb-3\"> <label\n                for=\"id_pseudonym\" class=\"form-label\">\n                Pseudonym\n            </label> <input type=\"text\" name=\"pseudonym\" maxlength=\"100\" class=\"textinput form-control\" id=\"id_pseudonym\"> </div> </div> </div>\n<div\n     \n    class=\"mb-3  \" \n    > <div class=\"\"> <button type=\"submit\" name=\"submit\" value=\"Create\" id=\"submit-id-submit\"\n    class=\"btn btn-primary\"><span>Create</span></button>\n<button type=\"button\" name=\"reset\" value=\"Cancel\" id=\"button-id-reset\"\n    class=\"btn btn-secondary\" data-cv-cancel-url=\"/\"><span>Cancel</span></button> </div>\n</div> </form>\n"
}
```

### Floor cached runtime and actual output

```json
{
  "python": "/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python",
  "versions": {
    "Django": "4.2.30",
    "django-crispy-forms": "2.0",
    "crispy-bootstrap5": "2023.10"
  },
  "helper_module": "/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/lib/python3.12/site-packages/crispy_forms/helper.py",
  "experiments": [
    {
      "helper": "FormHelper",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Aliasing",
      "copy": "alias: refused to mutate",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Raising",
      "copy": "RuntimeError: copy forbidden",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "ReadOnly",
      "copy": "AttributeError: property 'disable_csrf' of 'ReadOnly' object has no setter",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Hooks",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    }
  ],
  "raw_create": "\n<form class=\"cv-form\" method=\"post\" action=\"/\" enctype=\"multipart/form-data\" novalidate>\n    <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"LusSQi4g1UvB9wKZ3EnQRdGPKW2KENHNjCxdUO6s6aqQInn6yXM4oJo2Ncoy6iWL\">\n\n    \n\n    \n\n\n    \n\n<form  method=\"post\" > <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"LusSQi4g1UvB9wKZ3EnQRdGPKW2KENHNjCxdUO6s6aqQInn6yXM4oJo2Ncoy6iWL\"> <div id=\"div_id_name\" class=\"mb-3\"> <label for=\"id_name\" class=\"form-label requiredField\">\n                Name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"name\" class=\"textinput form-control\" required id=\"id_name\"> </div> </form>\n\n\n\n</form>\n\n",
  "raw_standalone_model_form": "\n\n<form  method=\"post\" > <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"test-token\"> <div  class=\"row \" > <div \n     class=\"col-md-4\" > <div id=\"div_id_first_name\" class=\"mb-3\"> <label for=\"id_first_name\" class=\"form-label requiredField\">\n                First name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"first_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_first_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_last_name\" class=\"mb-3\"> <label for=\"id_last_name\" class=\"form-label requiredField\">\n                Last name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"last_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_last_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_pseudonym\" class=\"mb-3\"> <label for=\"id_pseudonym\" class=\"form-label\">\n                Pseudonym\n            </label> <input type=\"text\" name=\"pseudonym\" maxlength=\"100\" class=\"textinput form-control\" id=\"id_pseudonym\"> </div> </div> </div>\n<div class=\"mb-3\"> <div class=\"\"> <button type=\"submit\" name=\"submit\" value=\"Create\" id=\"submit-id-submit\"\n    class=\"btn btn-primary\"><span>Create</span></button>\n<button type=\"button\" name=\"reset\" value=\"Cancel\" id=\"button-id-reset\"\n    class=\"btn btn-secondary\" data-cv-cancel-url=\"/\"><span>Cancel</span></button> </div>\n</div> </form>\n"
}
```

## Scope and migration handoff

## Tracer RED evidence

Actual JUnit report and semantic assessment below; `check tdd-red-evidence` returned `RED_EVIDENCE_OK`, one target failure. Plan's explicit 01-01/02 atomic boundary keeps RED evidence in this implementation commit rather than publishing an intermediate fixture-broken commit.

```json
{
  "command": "PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_form_ownership.py -k create_ownership_csrf_round_trip -q --junitxml=/tmp/cv-plan01-red.xml",
  "exitCode": 1,
  "output": "<?xml version=\"1.0\" encoding=\"utf-8\"?><testsuites name=\"pytest tests\"><testsuite name=\"pytest\" errors=\"0\" failures=\"1\" skipped=\"0\" tests=\"1\" time=\"0.738\" timestamp=\"2026-11-02T20:36:19.140000+00:00\" hostname=\"weaver-dev\"><testcase classname=\"tests.test1.test_theme_form_ownership\" name=\"test_create_ownership_csrf_round_trip\" time=\"0.548\"><failure message=\"AssertionError: nested raw form start tag&#10;assert not [{'attrs': {'class': 'cv-form', 'method': 'post', 'action': '/author/create/', 'enctype': 'multipart/form-data', ...}, 'tokens': ['HIZaSERQF9jzHOQdPIRWZYod6Uno0giEG9ZAfWQkcrpHql8uQEv3vbCWBqKboMlY'], 'submitters': []}]&#10;[+1 more line; full report in element text]\">cv_author = ViewSet(author), user_author_add = &lt;User: user_author_add&gt;\n\n    @pytest.mark.django_db\n    def test_create_ownership_csrf_round_trip(cv_author, user_author_add):\n        client = Client(enforce_csrf_checks=True)\n        client.force_login(user_author_add)\n        response = client.get(\"/author/create/\")\n        assert response.status_code == 200\n        sibling = '&lt;form method=\"post\"&gt;&lt;input name=\"csrfmiddlewaretoken\" value=\"sibling\"&gt;&lt;/form&gt;'\n&gt;       owner = assert_owned_form_markup(sibling + response.content.decode() + sibling)\n                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\ntests/test1/test_theme_form_ownership.py:63: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test1/test_theme_form_ownership.py:48: in assert_owned_form_markup\n    parser.feed(markup)\n/usr/lib/python3.12/html/parser.py:168: in feed\n    self.goahead(0)\n/usr/lib/python3.12/html/parser.py:260: in goahead\n    k = self.parse_starttag(i)\n        ^^^^^^^^^^^^^^^^^^^^^^\n/usr/lib/python3.12/html/parser.py:475: in parse_starttag\n    self.handle_starttag(tag, attrs)\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = &lt;tests.test1.test_theme_form_ownership._RawForms object at 0x7c0659050bc0&gt;\ntag = 'form', attrs = {'method': 'post'}\n\n    def handle_starttag(self, tag, attrs):\n        attrs = dict(attrs)\n        if tag == \"form\":\n&gt;           assert not self.stack, \"nested raw form start tag\"\nE           AssertionError: nested raw form start tag\nE           assert not [{'attrs': {'class': 'cv-form', 'method': 'post', 'action': '/author/create/', 'enctype': 'multipart/form-data', ...}, 'tokens': ['HIZaSERQF9jzHOQdPIRWZYod6Uno0giEG9ZAfWQkcrpHql8uQEv3vbCWBqKboMlY'], 'submitters': []}]\nE            +  where [{'attrs': {'class': 'cv-form', 'method': 'post', 'action': '/author/create/', 'enctype': 'multipart/form-data', ...}, 'tokens': ['HIZaSERQF9jzHOQdPIRWZYod6Uno0giEG9ZAfWQkcrpHql8uQEv3vbCWBqKboMlY'], 'submitters': []}] = &lt;tests.test1.test_theme_form_ownership._RawForms object at 0x7c0659050bc0&gt;.stack\n\ntests/test1/test_theme_form_ownership.py:29: AssertionError</failure></testcase></testsuite></testsuites>",
  "targetTest": "test_create_ownership_csrf_round_trip",
  "targetFile": "tests/test1/test_theme_form_ownership.py",
  "expected": "one raw owning form, one token; successful enforced CSRF round trip",
  "actual": "AssertionError: nested raw form start tag",
  "semanticAssessment": "Target executed GET successfully and failed on raw nesting, the planned missing behavior."
}
```

## After-change raw output (same cached runtime)

```json
{
  "python": "/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python",
  "versions": {
    "Django": "5.2.18",
    "django-crispy-forms": "2.7",
    "crispy-bootstrap5": "2026.9"
  },
  "helper_module": "/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/crispy_forms/helper.py",
  "experiments": [
    {
      "helper": "FormHelper",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Aliasing",
      "copy": "alias: refused to mutate",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Raising",
      "copy": "RuntimeError: copy forbidden",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "ReadOnly",
      "copy": "AttributeError: property 'disable_csrf' of 'ReadOnly' object has no setter",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    },
    {
      "helper": "Hooks",
      "copy": "ok",
      "adapter": "zero forms/tokens; source/layout unchanged; hooks retained"
    }
  ],
  "raw_create": "\n<form class=\"cv-form\" method=\"post\" action=\"/\" enctype=\"multipart/form-data\" novalidate>\n    <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"26WcvR626UrplZuEBPUqs5xk6rYithlepoVIu2BsUfJo5LfVdsTJTilqaLImwnjR\">\n\n    \n\n    \n\n\n\n<div id=\"div_id_name\" class=\"mb-3\"> <label\n                for=\"id_name\" class=\"form-label requiredField\">\n                Name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"name\" class=\"textinput form-control\" required id=\"id_name\"> </div>\n\n\n</form>\n\n",
  "raw_standalone_model_form": "\n\n<input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"test-token\"> <div  class=\"row \" > <div \n     class=\"col-md-4\" > <div id=\"div_id_first_name\" class=\"mb-3\"> <label\n                for=\"id_first_name\" class=\"form-label requiredField\">\n                First name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"first_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_first_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_last_name\" class=\"mb-3\"> <label\n                for=\"id_last_name\" class=\"form-label requiredField\">\n                Last name<span class=\"asteriskField\">*</span> </label> <input type=\"text\" name=\"last_name\" maxlength=\"100\" class=\"textinput form-control\" required id=\"id_last_name\"> </div> </div> <div \n     class=\"col-md-4\" > <div id=\"div_id_pseudonym\" class=\"mb-3\"> <label\n                for=\"id_pseudonym\" class=\"form-label\">\n                Pseudonym\n            </label> <input type=\"text\" name=\"pseudonym\" maxlength=\"100\" class=\"textinput form-control\" id=\"id_pseudonym\"> </div> </div> </div>\n<div\n     \n    class=\"mb-3  \" \n    > <div class=\"\"> <button type=\"submit\" name=\"submit\" value=\"Create\" id=\"submit-id-submit\"\n    class=\"btn btn-primary\"><span>Create</span></button>\n<button type=\"button\" name=\"reset\" value=\"Cancel\" id=\"button-id-reset\"\n    class=\"btn btn-secondary\" data-cv-cancel-url=\"/\"><span>Cancel</span></button> </div>\n</div>\n"
}
```

## Reviewed frame golden migration

All four diffs remove only the inner wrapper and its token; outer method/action/enctype/novalidate and fields remain unchanged. Protected-delete golden is unchanged. Two custom helper fixtures now declare form_tag=False; their icon-policy intent remains unchanged.

```diff
diff --git a/tests/test1/golden/form_frame/create.html b/tests/test1/golden/form_frame/create.html
index e52c071..a0ae68b 100644
--- a/tests/test1/golden/form_frame/create.html
+++ b/tests/test1/golden/form_frame/create.html
@@ -1 +1 @@
-<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form></form>
+<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form>
diff --git a/tests/test1/golden/form_frame/custom_form.html b/tests/test1/golden/form_frame/custom_form.html
index e52c071..a0ae68b 100644
--- a/tests/test1/golden/form_frame/custom_form.html
+++ b/tests/test1/golden/form_frame/custom_form.html
@@ -1 +1 @@
-<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form></form>
+<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form>
diff --git a/tests/test1/golden/form_frame/delete.html b/tests/test1/golden/form_frame/delete.html
index 971398f..0fd77d9 100644
--- a/tests/test1/golden/form_frame/delete.html
+++ b/tests/test1/golden/form_frame/delete.html
@@ -1 +1 @@
-<form class="cv-form" method="post" action="/" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form></form>
+<form class="cv-form" method="post" action="/" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form>
diff --git a/tests/test1/golden/form_frame/update.html b/tests/test1/golden/form_frame/update.html
index e52c071..a0ae68b 100644
--- a/tests/test1/golden/form_frame/update.html
+++ b/tests/test1/golden/form_frame/update.html
@@ -1 +1 @@
-<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form></form>
+<form class="cv-form" method="post" action="/" enctype="multipart/form-data" novalidate><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><div id="div_id_name" class="mb-3"><label for="id_name" class="form-label requiredField"> Name<span class="asteriskField">*</span></label><input type="text" name="name" class="textinput form-control" required id="id_name"></div></form>

```

Test-fixture corrections during GREEN: custom render_layout hook must return safe HTML (the initial test concatenation lost SafeString safety), and custom-template prefix assertion ignores the caller template's leading whitespace. Neither required a production change.

## Task 03 diagnostic RED

Classifier verdict: RED_EVIDENCE_OK. Target executes rendering with form_id and fails because strict mode does not yet raise. Original report retained; no fixture/import failure is counted as RED.

```json
{
  "command": "PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_form_ownership.py -k \"helper_wrapper_diagnostics and form_id and True\" -q --junitxml=/tmp/cv-plan01-diagnostic-red.xml",
  "exitCode": 1,
  "output": "<?xml version=\"1.0\" encoding=\"utf-8\"?><testsuites name=\"pytest tests\"><testsuite name=\"pytest\" errors=\"0\" failures=\"1\" skipped=\"0\" tests=\"1\" time=\"0.279\" timestamp=\"2026-11-02T20:38:58.824305+00:00\" hostname=\"weaver-dev\"><testcase classname=\"tests.test1.test_theme_form_ownership\" name=\"test_helper_wrapper_diagnostics[form_id-private-id-True]\" time=\"0.046\"><failure message=\"Failed: DID NOT RAISE ImproperlyConfigured\">strict = True, option = 'form_id', value = 'private-id'\ncaplog = &lt;_pytest.logging.LogCaptureFixture object at 0x789c016882c0&gt;\n\n    @pytest.mark.parametrize(\"strict\", [False, True])\n    @pytest.mark.parametrize(\n        (\"option\", \"value\"),\n        [(\"form_action\", \"missing-route:secret\"), (\"form_id\", \"private-id\"),\n         (\"attrs\", {\"data-private\": \"secret\"}), (\"form_class\", \"private-class\"), (\"form_method\", \"get\")],\n    )\n    def test_helper_wrapper_diagnostics(strict, option, value, caplog):\n        helper = _helper()\n        setattr(helper, option, value)\n        form = NameForm()\n        form.helper = helper\n        snapshot = dict(helper.__dict__)\n        layout_fields = list(helper.layout.fields)\n        context = _context(form)\n        layers = [dict(layer) for layer in context.dicts]\n        with override_settings(CRUD_VIEWS_STRICT=strict):\n            if strict:\n&gt;               with pytest.raises(ImproperlyConfigured, match=option) as error:\nE               Failed: DID NOT RAISE ImproperlyConfigured\n\ntests/test1/test_theme_form_ownership.py:329: Failed</failure></testcase></testsuite></testsuites>",
  "targetTest": "test_helper_wrapper_diagnostics[form_id-private-id-True]",
  "targetFile": "tests/test1/test_theme_form_ownership.py",
  "expected": "strict wrapper option raises ImproperlyConfigured",
  "actual": "Failed: DID NOT RAISE ImproperlyConfigured",
  "semanticAssessment": "Target renders helper with unused form_id but strict configuration error is absent; assertion failure is intentional."
}
```

## Final verification

- Before task 03: combined 01-01/02 gate passed 313 tests in 5.79s; tracer gate rerun passed 1 test (24 deselected) in 0.69s. This was followed by atomic implementation/fixture commit 4679686.
- Task 03 prescribed selection: ownership/frame/crispy-buttons passed 677 in 7.40s before adding two final regressions (falsey custom-template hook and actual enclosing crispy overlay).
- Final superset of both prescribed selections: `PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_form_ownership.py tests/test1/test_form_frame.py tests/test1/test_form_button_checks.py tests/test1/test_crispy_buttons.py -n 4 -q`.

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  7%]
........................................................................ [ 15%]
........................................................................ [ 22%]
........................................................................ [ 30%]
........................................................................ [ 37%]
........................................................................ [ 45%]
........................................................................ [ 52%]
........................................................................ [ 60%]
........................................................................ [ 68%]
........................................................................ [ 75%]
........................................................................ [ 83%]
........................................................................ [ 90%]
........................................................................ [ 98%]
................                                                         [100%]
952 passed in 10.82s

```

- Cached floor: `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_theme_form_ownership.py -n 4 -q`; before the last enclosing-overlay test was added:

```text
bringing up nodes...
bringing up nodes...

.......................................                                  [100%]
39 passed in 1.69s

```

- Ruff check and format --check passed all five modified Python files. No package installs.
- Added raw owner assertions to stock, themed and modal frame tests without changing normalizers.
- Diagnostics cover all five detectable options in both strict modes, quiet defaults, no action reversal, preserved source/layout state and context restoration. Explicit assignments equal to defaults cannot be detected. Standalone GET/custom helper policy remains outside this boundary.

Plan 01 corrects cv_render_form and library helpers. Stock workflow still invokes crispy directly until plan 05 and may retain a duplicate token. Legacy copied inner/workflow templates bypassing cv_form_helper remain outside the one-token contract; no global mutation or HTML rewriting detects/repairs them. Plan 08 must document standalone library forms losing their wrapper but retaining their token; caller-owned markup must not add a second token.

