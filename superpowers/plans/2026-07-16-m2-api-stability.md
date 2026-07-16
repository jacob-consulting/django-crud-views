# M2 — API Stability & Backlog Triage (0.14.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the public API surface for 1.0 (stability page), remove the deprecated `CrispyModelViewMixin` alias (#34), fix the `WorkflowView` hook placement (#31 breaking half), and record triage decisions on #28/#31 — shipping as 0.14.0.

**Architecture:** No new subsystems. Two breaking source changes (alias removal in `crud_views.lib.crispy`, method move in `crud_views_workflow.lib.views`), one new docs page, GitHub issue bookkeeping, and a release. Spec: `superpowers/specs/2026-07-16-m2-api-stability-design.md`.

**Tech Stack:** Django package (`src/` layout, hatchling), pytest (run from `tests/`), mkdocs (readthedocs theme, awesome-pages), ruff, `gh` CLI, bump-my-version.

## Global Constraints

- Line length 120, double quotes (ruff); pre-commit runs `ruff-format`.
- Quick test iteration: `cd tests && pytest` (full suite ~320 tests, must stay green).
- All `CrudView` class attributes use the `cv_` prefix.
- Breaking window is open pre-1.0: no deprecation shims for the changes in this plan.
- CHANGELOG entries go into a new `## 0.14.0` section at the top of `CHANGELOG.md` (below the `# Django CRUD Views - Changelog` heading, above `## 0.13.0`).
- Do NOT touch `django-crud-views-extensions` sources; it is only verified (Task 6).

---

### Task 1: Remove the `CrispyModelViewMixin` alias (#34)

**Files:**
- Modify: `src/crud_views/lib/crispy/form.py` (delete alias class lines 146–148; fix docstring line 32)
- Modify: `src/crud_views/lib/crispy/__init__.py` (drop import + `__all__` entry)
- Modify (mechanical rename): all files under `tests/`, `docs/`, `examples/` containing `CrispyModelViewMixin` (~31 files; e.g. `tests/test1/app/views.py` has 34 occurrences)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `CrispyViewMixin` (in `crud_views.lib.crispy`) is the only crispy view mixin name; Task 3's stability page lists it; Task 6's PR description says "Closes #34".

- [ ] **Step 1: Delete the alias from the source (this is the RED step — the suite must break)**

In `src/crud_views/lib/crispy/form.py`, delete these lines at the end of the file:

```python
# Deprecated alias kept for backwards compatibility, see issue #34
class CrispyModelViewMixin(CrispyViewMixin):
    pass
```

In the same file, the `CrispyFormMixin` docstring around line 32 currently reads:

```
    The mixin for CrudView(s) adds the view context cv_view to the form. CrispyModelViewMixin,
```

Change `CrispyModelViewMixin` to `CrispyViewMixin` in that docstring line.

In `src/crud_views/lib/crispy/__init__.py`:
- change line 15 from
  `from .form import CrispyModelForm, CrispyViewMixin, CrispyModelViewMixin, CrispyForm, CrispyDeleteForm`
  to
  `from .form import CrispyModelForm, CrispyViewMixin, CrispyForm, CrispyDeleteForm`
- remove the `"CrispyModelViewMixin",` line from `__all__`.

- [ ] **Step 2: Run the suite to verify it fails on the removed name**

Run: `cd tests && pytest -x -q`
Expected: FAIL during collection with `ImportError: cannot import name 'CrispyModelViewMixin'` (raised from `tests/test1/app/views.py` or `tests/test1/app/views_formset.py`).

- [ ] **Step 3: Mechanical rename in tests, docs, and examples**

From the repo root:

```bash
grep -rl "CrispyModelViewMixin" tests docs examples | xargs sed -i "s/CrispyModelViewMixin/CrispyViewMixin/g"
```

(Do NOT run this sed over `src/` — it would corrupt the class definition you just deleted from; `src/` was handled manually in Step 1.)

- [ ] **Step 4: Verify zero remaining references outside CHANGELOG/spec/plan history**

```bash
grep -rn "CrispyModelViewMixin" src tests docs examples
```

Expected: no output. (Hits under `superpowers/` and `CHANGELOG.md` are history and fine.)

- [ ] **Step 5: Run the full suite to verify it passes**

Run: `cd tests && pytest -q`
Expected: PASS, ~320 tests, 0 failures. The crispy behavior tests in `tests/test1/test_custom_form_view.py` now exercise `CrispyViewMixin` directly.

- [ ] **Step 6: Add the CHANGELOG entry**

At the top of `CHANGELOG.md` (directly under the `# Django CRUD Views - Changelog` line, above `## 0.13.0`), insert:

```markdown
## 0.14.0

### Removed
- **Breaking:** the deprecated `CrispyModelViewMixin` alias has been removed (#34). Use
  `CrispyViewMixin` instead — it was always the implementing class, and it works for both
  `CrispyModelForm` and `CrispyForm` views. Migration: replace `CrispyModelViewMixin` with
  `CrispyViewMixin` in imports and view base-class lists.
```

- [ ] **Step 7: Commit**

```bash
git add -A src tests docs examples CHANGELOG.md
git commit -m "feat!: remove deprecated CrispyModelViewMixin alias (closes #34)"
```

---

### Task 2: Move WorkflowView transition logic to `cv_form_valid` (#31 breaking half)

**Context for the implementer:** `CrudViewProcessFormMixin.post` (`src/crud_views/lib/views/mixins.py:35-38`) calls `cv_form_valid` (the framework "do the work" step — CreateView saves there, FormSetMixin saves formsets there) and then `cv_form_valid_hook` (the user extension point — a no-op `pass` in every core view; `MessageMixin` cooperates with it via `super()`). `WorkflowView` currently inverts this: its transition execution sits in `cv_form_valid_hook`, so a user subclass overriding the hook silently destroys transition execution.

**Files:**
- Modify: `src/crud_views_workflow/lib/views.py:82` (rename method)
- Test: `tests/test1/test_workflow.py` (two new tests; one docstring fix at ~line 263)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `WorkflowView.cv_form_valid(self, context: dict)` executes the transition; `cv_form_valid_hook` is inherited (no-op) again. Task 3's stability page documents both hooks; Task 4 references this change when rescoping #31.

- [ ] **Step 1: Write the two failing tests**

Append to `tests/test1/test_workflow.py`:

```python
# ---------------------------------------------------------------------------
# Hook placement (issue #31): transition logic must live in cv_form_valid,
# leaving cv_form_valid_hook free as the user extension point.
# ---------------------------------------------------------------------------


def test_transition_logic_lives_in_cv_form_valid():
    """
    WorkflowView must do its framework work in cv_form_valid (like Create/Update/FormSet views)
    and must NOT occupy cv_form_valid_hook, which is reserved for user subclasses.
    """
    from crud_views_workflow.lib.views import WorkflowView

    assert "cv_form_valid" in vars(WorkflowView)
    assert "cv_form_valid_hook" not in vars(WorkflowView)


@pytest.mark.django_db
def test_user_hook_override_keeps_transition(client_user_campaign_change: Client, campaign_new, monkeypatch):
    """
    A user subclass overriding cv_form_valid_hook (without calling super()) must not destroy
    transition execution — regression guard for issue #31.
    """
    from tests.test1.app.views import CampaignWorkflowView

    calls = []
    monkeypatch.setattr(CampaignWorkflowView, "cv_form_valid_hook", lambda self, context: calls.append("hook"))

    response = client_user_campaign_change.post(
        f"/campaign/{campaign_new.pk}/workflow/",
        {"transition": "wf_activate", "comment": ""},
    )
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.ACTIVE
    assert calls == ["hook"]
```

(`pytest`, `Client`, `CampaignState` are already imported at the top of this file; the fixtures `client_user_campaign_change` and `campaign_new` exist in `tests/test1/conftest.py`.)

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd tests && pytest test1/test_workflow.py::test_transition_logic_lives_in_cv_form_valid test1/test_workflow.py::test_user_hook_override_keeps_transition -v`
Expected: both FAIL — the first because `cv_form_valid_hook` IS in `vars(WorkflowView)` (and `cv_form_valid` is not), the second because the monkeypatched hook shadows the transition logic, so the campaign state stays `CampaignState.NEW`.

- [ ] **Step 3: Move the method**

In `src/crud_views_workflow/lib/views.py` line 82, rename the method — change:

```python
    def cv_form_valid_hook(self, context: dict):
        """
        Process workflow transition
        """
```

to:

```python
    def cv_form_valid(self, context: dict):
        """
        Process workflow transition
        """
```

The entire method body (comment normalization, `SuspiciousOperation` guard, `transaction.atomic()` block, `WorkflowInfo` creation, `on_transition` call) is unchanged. `WorkflowView` no longer defines `cv_form_valid_hook` at all — it inherits the no-op from `CustomFormView`.

- [ ] **Step 4: Fix the now-stale docstring in the message test**

In `tests/test1/test_workflow.py`, `test_workflow_view_post_emits_success_message` (~line 262) has a docstring sentence that describes the old placement:

```
    configured success message after a transition. MessageMixin precedes WorkflowView in the
    MRO, so its cv_form_valid_hook wraps WorkflowView's transition processing and then emits.
```

Replace those two lines with:

```
    configured success message after a transition. MessageMixin's cv_form_valid_hook runs
    after WorkflowView.cv_form_valid has processed the transition, then emits the message.
```

- [ ] **Step 5: Run the workflow tests, then the full suite**

Run: `cd tests && pytest test1/test_workflow.py -v`
Expected: PASS, including both new tests and `test_workflow_view_post_emits_success_message`.

Run: `cd tests && pytest -q`
Expected: PASS, 0 failures.

- [ ] **Step 6: Add the CHANGELOG entry**

In `CHANGELOG.md`, inside the `## 0.14.0` section created in Task 1, add after the `### Removed` block:

```markdown
### Changed
- **Breaking (workflow):** `WorkflowView` now executes its transition logic in `cv_form_valid`
  instead of `cv_form_valid_hook`, matching the framework convention (framework work in
  `cv_form_valid`, `cv_form_valid_hook` reserved for user subclasses). If a subclass overrides
  `cv_form_valid_hook` and relied on `super()` running the transition there, move that
  `super()` call to `cv_form_valid`. Part of #31; the configurable-transaction half of that
  issue is deferred to 1.x.
```

- [ ] **Step 7: Commit**

```bash
git add src/crud_views_workflow/lib/views.py tests/test1/test_workflow.py CHANGELOG.md
git commit -m "fix!: move WorkflowView transition logic to cv_form_valid (#31)"
```

---

### Task 3: Stability statement — `docs/development/stability.md` + index blurb

**Files:**
- Create: `docs/development/stability.md`
- Modify: `docs/index.md` (insert section before `## What it is not`, ~line 36)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `CrispyViewMixin` as the surviving crispy name (Task 1); `cv_form_valid` hook semantics (Task 2).
- Produces: the page Task 6's PR description links to; `docs/index.md` links to it as `development/stability.md`.

- [ ] **Step 1: Create `docs/development/stability.md`**

Write the file with this content. The class list below was compiled from the source on 2026-07-16; Step 2 verifies it against the reference docs before you build.

````markdown
# API stability

From release **1.0.0** on, django-crud-views follows [semantic versioning](https://semver.org/):
breaking changes to the **public API** defined on this page only happen in major releases.
This policy is effective as of 0.14.0 so that 1.0.0 can ship against a settled surface.

## The rule

The public API is the set of names listed below — the same names shown in the
[reference documentation](../reference/index.md). Everything else is internal:

- any module or name not listed here,
- all names prefixed with an underscore (`_`),
- template internals (block structure and context variables not documented in the reference),
- anything imported *by* django-crud-views from its dependencies.

Internal APIs may change in any release without notice.

## Public API

### `crud_views` (core)

**ViewSets** — `crud_views.lib.viewset`:
`ViewSet`, `ParentViewSet`

**View base** — `crud_views.lib.view`:
`CrudView`, `CrudViewPermissionRequiredMixin`

**Views** — `crud_views.lib.views`:
`ListView`, `DetailView`, `DetailCustomView`, `CreateView`, `UpdateView`, `DeleteView`,
`ActionView`, `OrderedUpView`, `OrderedDownView`, `CustomFormView`, `CustomFormNoObjectView`,
`CardListView`, `ManageView` — each with its `*PermissionRequired` variant — plus the mixins
`CreateViewParentMixin`, `ListViewTableMixin`, `ListViewTableFilterMixin`, `MessageMixin`,
`CardOrderMixin`

**Crispy forms integration** — `crud_views.lib.crispy`:
`CrispyViewMixin`, `CrispyModelForm`, `CrispyForm`, `CrispyDeleteForm`,
`Column1` … `Column12`

**Formsets (declaration surface)** — `crud_views.lib.formsets`:
`FormSetMixin`, `FormSets`, `FormSet`, `InlineFormSet`, `Formsets`, `FormControl` — i.e.
exactly the names exported by the package. The formsets machinery behind them (rendering
tree, per-formset plumbing) is internal, and stays internal in 1.0.

**Resources** — `crud_views.lib.resource`:
`Resource`, `ResourceViewMixin`

**Settings**: all `CRUD_VIEWS_*` settings documented in the
[settings reference](../reference/settings.md).

**Template tags**: the tags documented in the reference for the `crud_views` and
`crud_views_formsets` tag libraries.

**Declared attributes and hooks**: the documented `cv_*` class attributes of the classes
above, and the documented overridable hooks — e.g. `cv_form_valid` (framework work step),
`cv_form_valid_hook` (user extension point), `cv_post_hook`, `cv_form_invalid_hook`,
`cv_form_valid_redirect`.

### `crud_views_workflow`

`WorkflowView`, `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, the `WorkflowInfo`
model, and the `on_transition` hook.

### `crud_views_polymorphic`

`PolymorphicCreateSelectView`, `PolymorphicCreateView`, `PolymorphicUpdateView`,
`PolymorphicDeleteView`, `PolymorphicDetailView` — each with its `*PermissionRequired`
variant.

### `crud_views_guardian`

`GuardianViewSet`, `GuardianManageView`, and the `Guardian*PermissionRequired` view variants
(list, card list, detail, detail custom, create, update, delete, action).

## Deprecation policy (post-1.0)

- Public-API breaking changes happen only in **major** releases.
- A name slated for removal is deprecated first: it keeps working and emits a
  `DeprecationWarning` for the remainder of the current major cycle, and is removed no
  earlier than the next major release.
- Every deprecation and removal is recorded in the CHANGELOG with a migration hint.
````

- [ ] **Step 2: Audit the list against the reference docs**

For each class name on the page, confirm it appears in the reference docs (documented = public); drop names with no documentation hit from the page, or note them as candidates to document later:

```bash
for name in ViewSet ParentViewSet CrudView CrudViewPermissionRequiredMixin ListView DetailView \
  DetailCustomView CreateView UpdateView DeleteView ActionView OrderedUpView OrderedDownView \
  CustomFormView CustomFormNoObjectView CardListView ManageView CreateViewParentMixin \
  ListViewTableMixin ListViewTableFilterMixin MessageMixin CardOrderMixin CrispyViewMixin \
  CrispyModelForm CrispyForm CrispyDeleteForm FormSetMixin Resource ResourceViewMixin \
  WorkflowView WorkflowModelMixin PolymorphicCreateSelectView GuardianViewSet; do
  hits=$(grep -rl "$name" docs/reference docs/getting_started | wc -l)
  echo "$name: $hits"
done
```

Expected: most names have ≥1 hit. Known exception: the formsets names (`FormSets`, `FormSet`, `InlineFormSet`, `Formsets`, `FormControl`) have **no reference page yet** — keep them on the stability page anyway (the "exactly the names exported by the package" rule covers them; a formsets reference page is M4 work). For any *other* zero-hit name, remove it from the stability page and note it in the task summary.

- [ ] **Step 3: Add the index blurb**

In `docs/index.md`, insert before the `## What it is not` heading (~line 36):

```markdown
## API stability

From 1.0.0 on, django-crud-views follows [semantic versioning](https://semver.org) with a
[documented public API surface](development/stability.md): breaking changes to the public
API only happen in major releases, and deprecations are announced ahead of removal.

```

- [ ] **Step 4: Build the docs to verify**

Run: `uv run mkdocs build`
Expected: build succeeds; `site/development/stability/index.html` exists (awesome-pages picks the new page up via the `...` entry in `docs/development/.pages`). Optionally `task docs` to eyeball it.

- [ ] **Step 5: Add the CHANGELOG entry**

In `CHANGELOG.md`, inside the `## 0.14.0` section, add after the `### Changed` block:

```markdown
### Added
- API stability statement: `docs/development/stability.md` defines the public API surface
  covered by semver from 1.0.0 on, the internal/public split (including the formsets
  declaration surface), and the post-1.0 deprecation policy.
```

- [ ] **Step 6: Commit**

```bash
git add docs/development/stability.md docs/index.md CHANGELOG.md
git commit -m "docs: add API stability statement for 1.0 (M2)"
```

---

### Task 4: Record triage decisions on issues #28 and #31

**Files:** none (GitHub only, via `gh` CLI).

**Interfaces:**
- Consumes: the hook move from Task 2 (referenced in the #31 comment).
- Produces: recorded decisions the spec's done-when requires. #34 is NOT touched here — it closes automatically when Task 6's PR (description contains "Closes #34") merges.

- [ ] **Step 1: Comment the deferral decision on #28 and remove the obsolete item**

```bash
gh issue comment 28 --body "Triage decision (M2, pre-1.0 backlog triage): **deferred to 1.x**. System checks are additive dev-time tooling with no semver impact, so this does not block the 1.0 stability contract. The item \"run checks in crud_views_plain AppConfig\" is obsolete — the app was removed in 0.13.0 — and has been dropped from the issue body."
```

Then edit the body: fetch it with `gh issue view 28 --json body -q .body`, delete the sentence/list item `run checks in crud_views_plain AppConfig;` (keep the rest verbatim), and write it back with `gh issue edit 28 --body "<updated body>"`.

- [ ] **Step 2: Rescope #31**

```bash
gh issue comment 31 --body "Triage decision (M2, pre-1.0 backlog triage): **split**. The hook-placement half ships in 0.14.0 — \`WorkflowView\` transition logic moved from \`cv_form_valid_hook\` to \`cv_form_valid\`, restoring \`cv_form_valid_hook\` as the user extension point (breaking, done inside the pre-1.0 window). Remaining scope of this issue, **deferred to 1.x**: make the \`transaction.atomic()\` behavior around transitions configurable (additive, can ship in any minor)."
```

- [ ] **Step 3: Verify**

Run: `gh issue view 28 --json body,comments -q '.body' | grep -c crud_views_plain`
Expected: `0`.
Run: `gh issue view 31 --json comments -q '.comments[-1].body' | head -c 80`
Expected: the triage comment text.

(No commit — no repo files changed.)

---

### Task 5: Wart sweep

**Files:**
- Modify: `src/crud_views/lib/view/base.py:61`

**Interfaces:**
- Consumes: nothing.
- Produces: zero TODO-style comments in `src/`; a tracking issue for the one finding.

**Context:** the sweep was pre-run on 2026-07-16: `grep -rn "todo\|TODO" src/ --include="*.py"` returns exactly one hit — `src/crud_views/lib/view/base.py:61`:
`cv_parent_key: str | None = "list"  # parent key, defaults to list todo: does this make sense at all?`.
Changing the `cv_parent_key` default would be breaking and needs its own analysis, so per the spec ("findings get a decide-or-defer note, not automatic scope creep") the decision is: **defer with a tracking issue**, clean the comment.

- [ ] **Step 1: Re-run the sweep to confirm nothing new appeared**

```bash
grep -rn "todo\|TODO\|deprecat\|Deprecat" src/ --include="*.py" | grep -v __pycache__
```

Expected: only the `base.py:61` hit (the `deprecat` pattern may also match legitimate docstrings added by this plan — judge hits individually; anything genuinely new gets its own decide-or-defer note in the task summary).

- [ ] **Step 2: Open the tracking issue and clean the comment**

```bash
gh issue create --title "Reconsider cv_parent_key default (\"list\")" --body "From the M2 wart sweep (pre-1.0). \`CrudView.cv_parent_key\` defaults to \"list\" with an old inline doubt (\"does this make sense at all?\"). Changing the default would be breaking for nested ViewSets, so it was deferred at M2 rather than rushed into 1.0. Decide in 1.x: keep and document the default, or redesign. Deferred to 1.x — does not block 1.0 (the current behavior becomes the documented contract)."
```

Then in `src/crud_views/lib/view/base.py:61`, change the trailing comment:

```python
    cv_parent_key: str | None = "list"  # parent key, defaults to list todo: does this make sense at all?
```

to (replace `<N>` with the number `gh issue create` printed):

```python
    cv_parent_key: str | None = "list"  # parent key; default under review for 1.x, see issue #<N>
```

- [ ] **Step 3: Run the suite (comment-only change, but cheap insurance)**

Run: `cd tests && pytest -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/crud_views/lib/view/base.py
git commit -m "chore: resolve last TODO comment via tracking issue (M2 wart sweep)"
```

---

### Task 6: Extensions compatibility check, PR, and 0.14.0 release

**Files:** none in this repo beyond what earlier tasks committed; read-only use of `../django-crud-views-extensions`.

**Interfaces:**
- Consumes: all earlier tasks' commits; PR description closes #34 (Task 1) and links the stability page (Task 3).

- [ ] **Step 1: Verify the extensions repo against this branch**

`django-crud-views-extensions` was verified on 2026-07-16 to contain zero `Crispy*` imports; re-verify and run its suite against the local checkout:

```bash
grep -rn "CrispyModelViewMixin\|cv_form_valid_hook" ../django-crud-views-extensions/src ../django-crud-views-extensions/tests
```

Expected: no output. Then:

```bash
cd ../django-crud-views-extensions && uv pip install -e ../django-crud-views && uv run pytest -q; cd -
```

Expected: extensions suite PASS. Afterwards restore its normal dependency: `cd ../django-crud-views-extensions && uv sync && cd -`.

- [ ] **Step 2: Push a branch and open the PR**

Following the project's PR lifecycle (PR → wait CI → fix ruff if needed → squash-merge):

```bash
git checkout -b m2-api-stability
git push -u origin m2-api-stability
gh pr create --title "M2: API stability & backlog triage (0.14.0)" --body "$(cat <<'EOF'
Implements M2 of the release-1 milestone (spec: superpowers/specs/2026-07-16-m2-api-stability-design.md).

- Remove deprecated `CrispyModelViewMixin` alias — use `CrispyViewMixin`. Closes #34.
- Move `WorkflowView` transition logic from `cv_form_valid_hook` to `cv_form_valid` (#31, breaking half; remainder deferred to 1.x).
- Add API stability statement (`docs/development/stability.md`) + index blurb.
- CHANGELOG for 0.14.0 (two breaking changes, migration hints included).

Backlog triage recorded on #28 (deferred to 1.x) and #31 (rescoped).
EOF
)"
```

- [ ] **Step 3: Wait for CI, then squash-merge**

Run: `gh pr checks --watch`
Expected: all checks green (lint, docs, test matrix). If ruff complains, fix and push. Then:

```bash
gh pr merge --squash --delete-branch
git checkout main && git pull
```

Expected: #34 auto-closes on merge.

- [ ] **Step 4: Wait for main CI, then release 0.14.0**

Per the standard release process (bump-my-version + tag → publish.yml → PyPI, no GitHub Releases):

```bash
gh run watch $(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId')
uv run bump-my-version bump minor   # 0.13.0 → 0.14.0 (updates README.md, docs/index.md, pyproject.toml, src/crud_views/__init__.py; commits and creates tag v0.14.0)
git push && git push --tags
```

Then watch the publish workflow and verify:

```bash
gh run watch $(gh run list --workflow publish.yml --limit 1 --json databaseId -q '.[0].databaseId')
pip index versions django-crud-views 2>/dev/null || curl -s https://pypi.org/pypi/django-crud-views/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

Expected: `0.14.0` live on PyPI.

- [ ] **Step 5: Update the milestone document status**

In `superpowers/notes/2026-07-16-release-1-milestone.md`, M2 is complete: note it (e.g. change the M2 row/section heading to include "— DONE (0.14.0, 2026-07-16)") and commit:

```bash
git add superpowers/notes/2026-07-16-release-1-milestone.md
git commit -m "docs(plan): mark M2 complete in release-1 milestone"
git push
```
