# django-crud-views — Repository Audit & Improvement Plan

*Audit date: 2026-06-10 · Version audited: 0.5.0 (main @ a025914) · Analysis only, no code modified.*

## Executive Summary

**Overall health grade: B.** This is a well-engineered beta-stage Django library with genuinely strong infrastructure — a 3×3 Python/Django CI matrix, an enforced lint gate, trusted PyPI publishing gated on tests+docs+lint, 276 passing tests at ~90% coverage, a clean src/ layout, and consistent conventions. The grade is held back by one subsystem and a layer of accumulated rough edges. **Top 3 risks:** (1) the formsets subsystem is simultaneously the most complex code and the least tested (34–62% coverage) and contains at least three verified bugs, including an `assert Exception(...)` that can never raise in the nested-delete path; (2) create/update/delete POST handling distinguishes "create vs. update" by swallowing `AttributeError`, which can silently convert a broken update view into a create; (3) error handling is ad hoc across the package — bare `except Exception`, a global `ignore_exception` decorator, and exceptions-as-control-flow make real failures invisible. **Top 3 opportunities:** (1) a focused hardening pass on formsets (tests + the three known bugs) removes most of the correctness risk in one milestone; (2) ~41 inline TODOs, commented-out code blocks, and copy-paste artifacts ("my_new_tag", a taggit docstring) can be cleared cheaply and would noticeably raise the polish of a published package; (3) small packaging/tooling fixes (broken `bump-patch` task, nonexistent `bootstrap5` extra, malformed repo URL) are minutes of work each.

---

## Phase 1 — Repo Map

**Purpose:** `django-crud-views` is a published PyPI library (v0.5.0, "Development Status :: 4 - Beta", MIT) providing CRUD class-based views grouped into **ViewSets** — sibling-aware views with auto-generated URL patterns, permission integration, nesting, themes, and optional extensions. Intended users: Django developers building HTML CRUD UIs. Maturity: production-aspiring beta with real users (the author's own `dpl-examples` project consumes it).

**Stack:** Python ≥3.12, Django 4.2–6.0, Pydantic v2 (used unusually but deliberately for ViewSet/settings/check/formset config objects), django-tables2 / django-filter / crispy-forms as hard deps; fsm-2, polymorphic, ordered-model, guardian as optional extras. Build: hatchling + uv; tests: pytest + nox matrix; lint: ruff (format enforced in CI and pre-commit); docs: mkdocs → readthedocs.

**Architecture sketch:**

```
ViewSet (pydantic model, global _REGISTRY)         src/crud_views/lib/viewset/__init__.py
  ├─ registers CrudView subclasses via CrudViewMetaClass   lib/view/meta.py
  ├─ auto-detects PK type → regex URL patterns             lib/viewset/path_regs.py
  ├─ nesting via ParentViewSet (parent PK in URL, queryset filtering)
  └─ urlpatterns (cached_property) → re_path per view
CrudView (mixin base)                              lib/view/base.py
  └─ concrete views: List/Detail/Create/Update/Delete/Action/Manage   lib/views/
       + *PermissionRequired variants
Cross-cutting: settings singleton (lib/settings.py), Django system checks
(checks.py + lib/check.py), session persistence (lib/session.py),
template tags (templatetags/), nested formsets (lib/formsets/)
Extensions: crud_views_plain (theme), _workflow (django-fsm),
            _polymorphic, _guardian (per-object perms)
```

**Key directories:** `src/` — five packages (~5.8k LOC); `tests/test1/` — single test project, 276 tests (~5.5k LOC); `docs/` — mkdocs site; `examples/` — bootstrap5 + plain demo projects; `skills/` — a Claude Code skill shipped in-repo; `.github/workflows/` — tests, lint, docs, publish.

**Surprises:** (a) `lib/formsets/x.py` — a core file literally named "x" holding `XForm`/`XFormSet`, the engine of nested formset rendering/saving; (b) `docs/superpowers/` — 31 tracked internal AI-workflow artifacts (plans/specs) inside the published docs tree (excluded from nav via `docs/.pages`, but mkdocs still builds them as unlinked pages); (c) Pydantic models for Django plumbing — unconventional but consistent and validated, so it works.

---

## Phase 2 — Audit Report

Nothing here is **Critical** — no secrets, no injection vectors (template `{{ }}` auto-escaping covers user data; `template_code` strings are developer-supplied, not user input), and auth is handled by Django/guardian machinery. Findings below are facts unless marked *(judgment)*.

### Correctness & code quality

**H1 — `assert Exception(...)` never raises; lookup failure falls through to `None`. HIGH.**
`src/crud_views/lib/formsets/x.py:186`: `assert Exception("not found")` — asserting a truthy exception instance is a no-op; the intended `raise` never happens, and `get_x_form()` returns `None`. Callers at `x.py:200` then do `x_form.save(...)` → `AttributeError` during the **nested delete** path, or at `x.py:215` the sentinel check is useless. Consequence: a form/x-form mismatch during nested formset save produces a confusing 500 (or silent skip) instead of a clear error, in the exact code path that deletes user data.

**H2 — `except AttributeError` as create/update discriminator. HIGH.**
`src/crud_views/lib/views/mixins.py:29-32` and `src/crud_views/lib/views/delete.py:160-163`: `try: self.object = self.get_object() except AttributeError: self.object = None`. Any genuine `AttributeError` inside `get_object()` or a user's overridden queryset/model property is swallowed and the request proceeds as if no object exists — an update view with a typo silently behaves like a create view. This is exceptions-as-control-flow on the hottest write path in the package.

**H3 — Formsets: most complex subsystem, least tested. HIGH (theme).**
Coverage from a fresh run (276 passed, 1 skipped): `formsets/mixins.py` 34%, `formsets/formsets.py` 37%, `inline_formset.py` 40%, `x.py` 51%, `layout.py` 62% — versus ~85–100% nearly everywhere else. This is where H1, M1, M2, and M3 live. The package's riskiest code has the weakest safety net.

**M1 — Loop variable shadows the `index` parameter. MEDIUM.**
`src/crud_views/lib/formsets/formsets.py:142` (`for index, (key, child_formset) in enumerate(self.children.items())` inside `init()`, whose parameter is also `index` and is used to build `prefix_key` at line 108) and the same pattern at `formsets.py:217` in `template()`. With multiple top-level forms, the second iteration computes prefixes from the mutated value — latent prefix collision. Currently masked because `init` is called with a single form (`formsets.py:310`).

**M2 — PolymorphicFormSetMixin contradicts itself. MEDIUM.**
`src/crud_views/lib/formsets/mixins.py:177-182`: the comment says "it is okay that a model has no formsets defined", then raises `ValueError` when the model is missing; the subsequent `formsets is None` branch is unreachable dead code. One of the two behaviors is wrong.

**M3 — Unvalidated AJAX input drives formset template rendering. MEDIUM.**
`src/crud_views/lib/formsets/mixins.py:44-53`: `key_path`, `pk` (string default `"None"`), and `num` come raw from `request.GET` into `FormSets.get_template()` (`formsets.py:319-327`), where an unknown key produces `KeyError`/`AttributeError` (500), and `num` (a string) is interpolated into form prefixes (`formsets.py:197`). Consequence: user-controllable 500s and malformed prefixes rather than a 400. Robustness, not exploitability.

**M4 — Custom check message formatted and discarded. MEDIUM.**
`src/crud_views/lib/check.py:40-44`: `get_message(msg)` runs `msg.format(**kwargs)` but ignores the result, always returning `self.msg.format(...)`. `CheckEitherAttribute.messages()` (`check.py:136-144`) passes distinct messages for "neither set" vs. "both set" — both are silently replaced by the default template (which happens to contain the typo "not" for "nor", `check.py:110`). Developers get the wrong diagnostic from the system-check feature that is one of the package's selling points.

**M5 — ViewSet registry silently overwrites duplicates. MEDIUM.**
`src/crud_views/lib/viewset/__init__.py:111-112`: `_REGISTRY[self.name] = self` with no duplicate check (contrast with `register_view_class` at line 237, which does check). Two ViewSets with the same name — easy in a multi-app project — silently shadow each other; symptoms surface later as wrong URLs/querysets.

**M6 — Shared mutable class-attribute lists mutated at registration. MEDIUM *(judgment on fragility; mutation is fact)*.**
View classes assign settings lists directly, e.g. `cv_context_actions = crud_views_settings.delete_context_actions` (`lib/views/delete.py:25`), so every view sharing a default holds the *same list object* owned by the settings singleton. `register_view_class` then mutates it in place: `view_class.cv_context_actions.append("manage")` (`viewset/__init__.py:240-243`) — guarded by an `if "manage" not in ...`, behind a literal `if True:  # todo: based on settings`. The current behavior works by accident (the dedup guard makes the global mutation idempotent), but mutating the settings singleton from registration code is a trap for anyone touching either side. (Note: actual access to manage views *is* properly gated at `lib/views/manage.py:31-35`.)

**M7 — Swallowed exceptions. MEDIUM.**
Facts: `lib/views/delete.py:75-76` (`except Exception: return None` while resolving related-object URLs) and `crud_views_guardian/lib/mixins.py:133-135` (`except Exception: parent_obj = None` while resolving the parent for the create-button check). Plus the `ignore_exception` decorator with a module-level `STRICT = False` and `# todo: get strict from settings` (`lib/exceptions.py:30-53`), applied in `templatetags/crud_views.py:69` and `lib/table/columns.py:49`. Consequence: misconfigured viewsets render with silently missing buttons/links instead of failing loudly in development.

**M8 — Import-time side effects. MEDIUM.**
`User = get_user_model()` executes at module import in `lib/view/base.py:28`, `lib/view/meta.py:12` (where it's also unused), and `templatetags/crud_views.py:10`; the settings singleton instantiates at import (`lib/settings.py:125`) with `from_settings()` calls evaluated in the class body (`settings.py:29+`). With a custom `AUTH_USER_MODEL` and an unlucky import order (e.g. from an `AppConfig.ready` or a models module), this raises `AppRegistryNotReady`/`ImproperlyConfigured`. A known Django footgun.

**M9 — Settings model has weak validation and an accumulating check property. MEDIUM.**
`lib/settings.py:29-31`: `extends: str = from_settings("CRUD_VIEWS_EXTENDS")` — no default; Pydantic doesn't validate defaults, so a missing `CRUD_VIEWS_EXTENDS` yields `extends = None` typed as `str`, and `check_template(None)` (`settings.py:75-81`) fails with a confusing error rather than "setting missing". Also, the `check_messages` property appends into `self._check_messages` on every access — repeated check runs accumulate duplicate errors. `manage_views_enabled` is a free string ("no, yes, debug_only" per comment) with no enum validation.

**M10 — UUID URL regex matches only version-4 UUIDs. MEDIUM.**
`lib/viewset/path_regs.py:8` and `lib/formsets/formsets.py:23` hardcode `4[0-9a-f]{3}-[89ab]...`. A model whose UUID PK uses uuid1/uuid7 (increasingly common for index locality) gets 404s on every detail/update/delete URL. Undocumented constraint.

**L1 — Dead/commented-out code and 41 TODOs. LOW.**
41 `todo` markers across `src/` (e.g. `viewset/__init__.py:240`, `crispy/form.py:133` "remove this"); commented-out blocks at `lib/formsets/mixins.py:127-140`, `lib/views/mixins.py:178-180`, `lib/check.py:194-196`; dead `_messages = []` at `settings.py:16`; `cv_get_context_button` has a TODO-then-`pass` stub at `lib/view/base.py:276-277`; `XFormSet.start_at_rows` self-labels "bad name" (`x.py:79`).

**L2 — Copy-paste artifacts in user-facing system checks. LOW.**
`src/crud_views/checks.py:11-26`: check tag literally named `"my_new_tag"` with a docstring from a tutorial ("Check that django-taggit is installed when usying myapp" — including the typo). These IDs/tags appear in users' `manage.py check` output.

**L3 — `permission_required` as `cached_property` + DB-backed cached permissions. LOW.**
`lib/view/base.py:417-423` caches per-instance (harmless but pointless); `viewset/__init__.py:353-371` `default_permissions` runs `ContentType`/`Permission` queries inside a `cached_property` cached for process lifetime, with fragile codename parsing (`permission.codename.split(f"_{permission.content_type.model}")[0]`, acknowledged by the `# todo` at line 368). Permissions added at runtime are invisible until restart; calling it before migrations errors.

**L4 — Minor robustness gaps. LOW.**
`lib/views/mixins.py:193`: `json.loads(request.body)` without handling malformed JSON → 500 instead of 400. `lib/session.py:74-80`: `SessionData.__exit__` writes the session even when an exception is propagating. `lib/views/delete.py`: `cv_check_delete_protection()` runs twice per POST (lines 137 and 168).

### Security

Healthy overall: no hardcoded secrets; CSRF token passed via Django's `get_token` into a data attribute (`templatetags/crud_views.py:37-45`); guardian integration is carefully reasoned with explicit anonymous-behavior handling and documented `accept_global_perms` semantics; workflow transitions are re-validated server-side before `getattr` dispatch (`crud_views_workflow/lib/views.py:99-105`) with `SuspiciousOperation` on tampering. Remaining items are M3 (input validation → 500s) and M7 (fail-open button rendering on swallowed exceptions — buttons are not the access control, the views are, so this is UX not authz).

### Testing

Strong foundation: 276 tests, behavior-asserting (HTML parsed with lxml/cssselect via `tests/lib/helper/`), good fixture conventions, guardian/workflow deeply covered (54 and 52 tests). Gaps: **the formsets subsystem (H3)** — no tests exercise nested save/delete (`x.py:177-237` save logic at 51%), the AJAX template endpoint, or polymorphic formsets; no `fail_under` in the coverage config (`pyproject.toml:116-118`), so coverage can silently regress; codecov upload is informational only.

### Dependencies

Healthy. Current versions in the dev venv (Django 5.2.14, pydantic 2.13.4, tables2 3.0.0, filter 25.2); floors in `pyproject.toml` are permissive but tested against the matrix. Two facts: `noxfile.py:14` installs a **nonexistent `bootstrap5` extra** (pip warns, doesn't fail — stale name); the `all` extra (`pyproject.toml:57-59`) omits `guardian`. `python-box` is a heavy-ish dep used only for attribute-style access in `settings.py:96-112` *(judgment: removable)*. No lockfile is committed (`uv.lock` gitignored) — defensible for a library.

### DevEx & operations

CI is the repo's strength (see Strengths). Three concrete breaks: **`task bump-patch` runs `bumpver`** (`taskfile.yaml:51`) but the project installs `bump-my-version` and configures `[tool.bumpversion]` (`pyproject.toml:64,120`) — the task fails (`bumpver` isn't installed; only `bump-my-version` is on PATH). `pyproject.toml:86` repository URL is malformed (`https://github.com:jacob-consulting/...` — colon instead of slash). Pre-commit runs only `ruff-format`, not `ruff check` (`.pre-commit-config.yaml`), so lint errors surface first in CI. No type-checking (mypy/pyright) anywhere despite heavy annotation use.

### Documentation

Good: accurate README with badges, mkdocs reference per view type, maintained CHANGELOG, in-repo Claude skill. Issues: `docs/superpowers/` ships 31 internal planning artifacts into the built site as unlinked-but-published pages; `docs/tbd/overview.md` placeholder; the v4-only UUID constraint (M10) and the formset `x.py` model are undocumented.

### Strengths (preserve these)

1. **CI/release engineering**: 3 Python × 3 Django nox matrix in both `tests.yml` and `publish.yml`; publish gated on tests+docs+lint with PyPI trusted publishing (OIDC, no token) — better than many mature libraries.
2. **Test culture**: 276 behavior-level tests with disciplined fixture naming, HTML assertions, random-order + xdist.
3. **Consistent conventions**: `cv_` prefixing, view-key vocabulary, ruff-enforced style, src/ layout, clean wheel packaging of five apps.
4. **Design ideas**: Django system checks for config validation at startup; sibling-aware URL generation; pluggable themes via template override; the guardian mixins' docstrings explain *why* (e.g. the ModelBackend obj-perm subtlety) — exemplary.

---

## Phase 3 — Improvement Strategy

**Theme 1: The formsets subsystem is the unmanaged risk concentration.**
Most-complex + least-tested + all known correctness bugs (H1, M1, M2, M3). *Target state:* formsets coverage ≥ 80%, the three bugs fixed, the AJAX endpoint validating input, and `x.py` renamed/documented. *Principle:* test coverage should be proportional to complexity × blast radius, and nested save/delete touches user data.

**Theme 2: Failures are silenced instead of surfaced.**
H2, M4, M7, L4 are all one pattern: exceptions swallowed or misused as control flow. *Target state:* no bare `except Exception` in src/; create-vs-update decided structurally (e.g. `self.pk_url_kwarg in self.kwargs`), not by exception type; `ignore_exception`'s STRICT wired to a setting defaulting to `DEBUG`. *Principle:* a library must fail loudly in development — its users can't read its source to debug silence.

**Theme 3: Import-time global state.**
M5, M6, M8, M9 share a root: module-level singletons mutated/initialized at import. *Target state:* registry rejects duplicate names; registration doesn't mutate shared lists (copy-on-write defaults); `get_user_model()` deferred to call sites; settings validated with enums/defaults and an error message naming the missing Django setting. *Principle:* a reusable app cannot control its host's import order.

**Theme 4: Published-package polish debt.**
L1, L2, broken bump task, stale nox extra, malformed URL, docs/superpowers in the site. Individually trivial; collectively they're what a prospective adopter sees first. *Target state:* zero copy-paste artifacts in user-visible output, working release tooling, TODOs triaged into issues or deleted.

**Explicitly NOT recommending:** adopting mypy across the codebase (Pydantic+Django metaclass code makes this XL-effort for modest payoff at this size — revisit if contributors join); replacing the Pydantic-for-config approach (unconventional but consistent, validated, and load-bearing — churn without benefit); rewriting regex-based URL routing to `path()` converters (works, tested, no user pain); removing python-box (cosmetic); committing a lockfile (it's a library; the matrix is the real compatibility contract).

**Definition of done:** zero High findings; formsets modules ≥ 80% coverage with `fail_under` set so CI fails on regression; `grep -rn "except Exception" src/` returns nothing unjustified; `task bump-patch` performs a dry-run successfully; `manage.py check` output contains no placeholder tags; duplicate ViewSet name raises at startup.

---

## Phase 4 — Task Plan

> **Execution status (2026-06-10): ALL MILESTONES COMPLETE.**
> *Milestone 3*: 3.1 `x.py` → `render_tree.py` with module docstring, `start_at_rows` → `render_rows_only` (PR #26) · 3.3 TODO triage — 37 markers removed, 8 converted to issues #27–#34, commented-out code deleted (PR #35) · 3.4–3.6 robustness fixes (JSON 400, session-write guard, single delete-protection call), `ruff-check` in pre-commit, `docs/tbd/` removed, permission caching documented (PR #36).
> Final suite: 318 passed, 1 skipped; total coverage 95% gated at `fail_under = 88`; `grep -rci todo src` = 0; zero High findings remain. Follow-up work lives in issues #27–#34.
> *Milestones 0–1* (PR #20): formsets test suite + bug fixes (coverage 34–62% → 78–100%, total 95% with `fail_under = 88`), structural object resolution via `cv_object`, duplicate-ViewSet-name guard, check message fix, UUID regex widened, tooling fixes.
> *Milestone 2*: 2.1 `CRUD_VIEWS_STRICT` setting + error-handling sweep (PR #21) · 2.2 copy-on-write context actions honoring `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (PR #22) · 2.4 settings check hardening — E100/E101, idempotent checks (PR #23) · 2.3 import-time `get_user_model()` removal, `settings.AUTH_USER_MODEL` FK (PR #24).
> *Finding revision (M8):* the custom-user-model app-ordering failure does **not** reproduce during app loading on Django 4.2/5.2 (verified empirically); the real reproducible case was pre-`django.setup()` imports of the templatetag modules (fixed + regression-tested). `lib.view.base` remains transitively registry-dependent through Django's own `auth.mixins` import chain — out of crud_views' control.
> Suite after Milestone 2: 314 passed, 1 skipped; ruff clean.
> **Remaining (Milestone 3):** 3.1 rename `x.py` · 3.3 TODO triage · 3.4 `docs/tbd/` cleanup · 3.5 pre-commit `ruff check` + minor robustness · 3.6 permission-cache docs.

### Milestone 0 — Safety net

| # | Task | Files | Acceptance criteria | Effort | Risk | Deps |
|---|------|-------|---------------------|--------|------|------|
| 0.1 | **Characterization tests for nested formset save/delete/AJAX.** Cover: nested create, nested update with reorder, nested delete (parent + child rows), the `?template=` AJAX endpoint (valid + garbage input), polymorphic formsets with/without a mapping entry. Use existing `tests/test1` models/fixture style. | `tests/test1/test_formsets*.py`, possibly `tests/test1/app/` | formsets modules ≥ 75% coverage; tests pass on current code (documenting today's behavior, with `xfail` markers for known bugs) | L | None (test-only) | — |
| 0.2 | **Coverage floor in CI.** Add `fail_under` to `[tool.coverage.report]` at the current total (≈90). | `pyproject.toml:116` | CI fails if coverage drops below floor | S | Low | — |

### Milestone 1 — Critical/correctness fixes

| # | Task | Files | Acceptance criteria | Effort | Risk | Deps |
|---|------|-------|---------------------|--------|------|------|
| 1.1 | **Fix `assert Exception` → `raise`, decide lookup-miss semantics.** | `x.py:182-186` | Missing x-form raises `CrudViewError` with form prefix in message; 0.1's xfail flips to pass | S | Low | 0.1 |
| 1.2 | **Replace `except AttributeError` create/update discrimination.** Decide object presence structurally (PK kwarg in `self.kwargs` / `cv_object`); keep `get_object()` exceptions propagating. | `lib/views/mixins.py:24-32`, `lib/views/delete.py:159-163` | A raising `get_object()` produces an error, not a silent create; full suite green | M | **Medium** — touches every POST | 0.1 |
| 1.3 | **Fix `index` shadowing in formsets.** Rename inner loop vars at `formsets.py:142,217`. | `lib/formsets/formsets.py` | Multi-form `init()` produces non-colliding prefixes (unit test) | S | Low | 0.1 |
| 1.4 | **Resolve PolymorphicFormSetMixin contradiction** (return None per the comment, or document the raise). | `lib/formsets/mixins.py:174-183` | Comment and behavior agree; dead branch removed | S | Low | 0.1 |
| 1.5 | **Validate AJAX template-endpoint input**: unknown keys / non-int `num` / bad `pk` → `BadRequest` (400). | `lib/formsets/mixins.py:44-53`, `formsets.py:319-327` | Garbage GET params return 400 | S | Low | 0.1 |
| 1.6 | **Fix `check.py` message handling**: return the formatted custom msg; fix "not"→"nor" typo. | `lib/check.py:40-44,110` | `CheckEitherAttribute` emits its two distinct messages (unit test) | S | Low | — |
| 1.7 | **Registry duplicate-name guard.** Raise on duplicate ViewSet name (consider allowing identical re-registration for test reloads — check `tests/test1/conftest.py` patterns first). | `viewset/__init__.py:111-112` | Duplicate name raises with both ViewSets named; suite green | S | Medium | — |

### Milestone 2 — High-leverage improvements

| # | Task | Files | Acceptance criteria | Effort | Risk | Deps |
|---|------|-------|---------------------|--------|------|------|
| 2.1 | **Error-handling sweep**: narrow exceptions + `logger.warning` at the two `except Exception` sites; wire `ignore_exception` STRICT to a `CRUD_VIEWS_STRICT` setting defaulting to `DEBUG`; add module loggers (the package currently has none). | `delete.py:75`, `guardian/lib/mixins.py:134`, `lib/exceptions.py:30`, `lib/settings.py` | No bare `except Exception` in src/; misconfig logs in non-strict mode, raises in strict | M | Medium (strict default is a behavior change — changelog it) | — |
| 2.2 | **Copy-on-write context actions**: registration copies the list before appending "manage"; honor the `if True` TODO with the real setting. | `viewset/__init__.py:236-243`, view classes assigning settings lists | Settings singleton lists never mutated (unit test asserts identity-safety) | M | Medium | — |
| 2.3 | **Defer `get_user_model()`** to call time in the three modules; remove the unused binding in `meta.py`. | `lib/view/base.py:28`, `lib/view/meta.py:12`, `templatetags/crud_views.py:10` | Importing `crud_views` before app registry ready doesn't raise | S | Low | — |
| 2.4 | **Settings hardening**: enum for `manage_views_enabled`, explicit error when `CRUD_VIEWS_EXTENDS` missing, make `check_messages` idempotent, delete dead `_messages`. | `lib/settings.py` | Missing EXTENDS produces "set CRUD_VIEWS_EXTENDS" check error; repeated check runs don't duplicate | M | Low | — |
| 2.5 | **Release tooling fix**: `taskfile.yaml:51` → `bump-my-version bump patch`; fix `pyproject.toml:86` URL; remove `bootstrap5` from `noxfile.py:14`; add `guardian` to the `all` extra. | `taskfile.yaml`, `pyproject.toml`, `noxfile.py` | `task bump-patch` dry-run succeeds; `[all]` pulls guardian | S | Low | — |
| 2.6 | **UUID PK regex**: widen to accept any UUID version (decision #5): `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`. | `path_regs.py:8`, `formsets.py:23` | uuid7-PK model resolves URLs (test) | S | Low | — |

### Milestone 3 — Quality & polish

| # | Task | Files | Acceptance | Effort | Risk |
|---|------|-------|-----------|--------|------|
| 3.1 | Rename `x.py` → `render_tree.py` (or similar) with a module docstring explaining XForm/XFormSet's role; fix `start_at_rows` naming. Formsets API is semi-private (decision #1): no deprecation shims needed, but update the example app for any renamed imports | `lib/formsets/`, `examples/` | New reader can explain the formset render model from docstrings alone; example apps run | M | Low |
| 3.2 | Rename check tag/docstring (`my_new_tag`, taggit text) to `crud_views`; assign stable check IDs | `checks.py:11-26` | `manage.py check` output is professional | S | Low |
| 3.3 | TODO triage: convert the ~10 meaningful TODOs (e.g. `cv_get_context_button` stub at `base.py:276`, `crispy/form.py:133`) to GitHub issues; delete the rest + commented-out blocks | src-wide | `grep -rci todo src` < 10; no commented-out code blocks | M | Low |
| 3.4 | ~~Move `docs/superpowers/` out of the docs tree~~ *(done 2026-06-10 → `/superpowers/`)*; fill or remove `docs/tbd/` | `docs/` | Built site contains only intended pages | S | Low |
| 3.5 | Add `ruff check` to pre-commit; minor robustness fixes (JSON 400 in `mixins.py:193`, skip session write on exception in `session.py:74`, dedupe delete-protection call) | various | Listed behaviors verified by small tests | S–M | Low |
| 3.6 | Document permission caching behavior (`default_permissions` process-lifetime cache) or make it lazy-per-request | `viewset/__init__.py:353` | Documented in reference/settings.md | S | Low |

### Quick wins (do immediately, all S effort)

- **1.1** the `assert Exception` fix — one line, removes a data-path landmine.
- **2.5** tooling fixes — `bumpver`→`bump-my-version`, repo URL, `bootstrap5` extra, `all` extra. Minutes each.
- **1.6** check.py message fix. **3.2** "my_new_tag" rename. **0.2** coverage floor.

### Implementation sketches — top 3 tasks

**0.1 Formset characterization tests.** Follow `tests/test1/test_form_validation.py` style. Key steps: (a) add a two-level nested model chain to `tests/test1/app/models.py` if one doesn't exist (Publisher→Book exists; a third level may be needed for nested formsets); (b) drive Create/Update views with `client.post` using hand-built management-form payloads — the prefix scheme is `{key}-{parent_prefix}-{pk}-{index}` per `formsets.py:105-109`, so write a small payload-builder helper in `tests/lib/helper/`; (c) for the AJAX endpoint, GET with `?template=key|child&num=0&pk=...` and assert the JSON `rows`/`html` shape. Gotcha: `XFormSet.save` relies on `form.has_changed()` (`x.py:218`), so payloads must actually differ from initial data or save-count assertions will be vacuously wrong.

**1.2 Create/update discrimination.** Approach: in `CrudViewProcessFormMixin.post`, replace try/except with `self.object = self.get_object() if self.cv_object and self.cv_viewset.pk_name in self.kwargs else None`. Steps: (a) confirm which views reuse the mixin (CreateView lacks the PK kwarg; check `lib/views/create.py` doesn't depend on the AttributeError path); (b) keep `DeleteView.post` consistent; (c) run the full suite — the guardian mixins override `get_object()` (`guardian/lib/mixins.py:48-53`) and must still execute their permission check on POST; verify a guardian-update-denied test still 403s. Gotcha: Django's `CreateView.get_object` raises `AttributeError` precisely because `queryset`/PK is absent — the structural check must not call it at all for create.

**2.1 Error-handling sweep.** Approach: add `logger = logging.getLogger("crud_views")` per module. In `delete.py:cv_get_related_object_url`, catch `NoReverseMatch` specifically and log at debug. In guardian `cv_get_context`, catch narrowly (`Http404`, parent-resolution errors). For `ignore_exception`, read strictness lazily inside the wrapper (`getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG)`) — *not* at decoration time, or the import-order problem (M8) recurs. Gotcha: STRICT defaulting to `DEBUG` means existing dev setups may start raising where they silently rendered nothing — call it out in CHANGELOG; consider defaulting to `False` for one minor release with a deprecation note.

---

## Open Questions — RESOLVED (maintainer decisions, 2026-06-10)

1. **Formsets API maturity** — *Semi-private.* Renames/API breaks in M1/3.1 are allowed without deprecation shims; only the example app needs updating alongside.
2. **Multi-form `FormSets.init`** — *Keep the list signature* (a formset can contain multiple children). Fix the shadowing (task 1.3) rather than simplifying.
3. **Strictness default** (task 2.1) — *Approved:* `CRUD_VIEWS_STRICT` defaults to `DEBUG` (fail loud in development). Note as behavior change in CHANGELOG.
4. **`docs/superpowers/`** — *Moved to `/superpowers/` at repo root* (done 2026-06-10, internal spec references updated). Superpowers half of task 3.4 is complete; only `docs/tbd/` remains.
5. **uuid v4-only routing (M10)** — *Widen the regex* to accept any UUID version (task 2.6), in both `path_regs.py:8` and `formsets.py:23`.
6. **Performance targets** — *No work needed*; lists (tables/cards) are bounded in practice.

**Lighter-review areas:** template HTML/JS files (bootstrap5 + plain themes), `examples/`, `crud_views_polymorphic` internals, and `scripts/generate_mockups.py` got structural review only; depth went to `lib/` core, formsets, guardian, workflow, and packaging/CI.
