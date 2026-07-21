# Asset Registry: Optional CSP Compliance (Nonces + SRI)

**Date:** 2026-07-21
**Status:** Approved design, pending implementation plan

## Problem

Since the 0.4.0 CSP refactor, django-crud-views uses no inline scripts, inline styles, or
inline event handlers, so a host-allowlist CSP (`script-src 'self' ...`) works out of the box.
Two gaps remain for the asset registry (`crud_views/lib/assets.py` and the `{% cv_js %}` /
`{% cv_css %}` tags):

1. **Nonce-based strict CSP** (`script-src 'nonce-…' 'strict-dynamic'`): browsers ignore the
   host allowlist under `'strict-dynamic'`, so every `<script>` tag we render needs a
   `nonce` attribute. Today the tags render none.
2. **Subresource integrity (SRI)**: registrants pointing at external CDN URLs cannot attach
   `integrity` / `crossorigin` attributes; registry entries are plain strings.

Support must be **optional**: projects without CSP middleware get byte-identical output.

## Requirements

- Auto-detect the nonce; no new settings required for the common cases.
- Work across the full test matrix:
  - **Django 4.2 / 5.2** with the separate `django-csp` package (public `request.csp_nonce`).
  - **Django 6.0** with built-in CSP (`django.middleware.csp.ContentSecurityPolicyMiddleware`).
- Per-entry SRI metadata for registrants, aimed at external URLs.
- `register_assets()` stays backwards compatible; plain-string entries keep working.
- No new runtime dependencies (`django-csp` is never imported).

## Django-version compatibility notes (verified against source)

Django 6.0's built-in CSP is **not** attribute-compatible with django-csp:

- The middleware stores the nonce on the **private** `request._csp_nonce`, not
  `request.csp_nonce`.
- Public APIs are `django.middleware.csp.get_nonce(request)` (returns `None` when the
  middleware didn't run) and the `django.template.context_processors.csp` context processor
  (exposes `{{ csp_nonce }}`).
- The nonce is a `LazyNonce`: **falsy until first evaluated**. Truthiness-based detection
  would silently emit nothing; detection must check existence and force evaluation via
  `str()`.
- `build_policy()` only injects the nonce into the header where the `CSP.NONCE` sentinel
  appears in `SECURE_CSP`, so force-evaluating the nonce is harmless when the project does
  not use nonce sources.

## Design

### 1. `Asset` dataclass (SRI vehicle — Proposal A)

In `crud_views/lib/assets.py`:

```python
@dataclass(frozen=True)
class Asset:
    path: str                       # static path or external URL
    integrity: str | None = None    # "sha256-…" / "sha384-…" / "sha512-…"
    crossorigin: str | None = None  # rendered as "anonymous" when integrity is set and this is None
```

- `register_assets(key, js=..., css=...)` accepts `str | Asset` per entry. Strings normalize
  to `Asset(path)` at registration time; `AssetBundle.js/css` become tuples of `Asset`.
- Core assets from `CrudViewsSettings.javascript()` / `.css` are normalized the same way in
  the tags; the settings API itself is unchanged.
- `resolve_url()` / `is_external()` operate on `Asset.path`; behavior unchanged.
- When `integrity` is set and `crossorigin` is `None`, tags render
  `crossorigin="anonymous"` (required for cross-origin SRI fetches). An explicit
  `crossorigin` value is rendered verbatim; `crossorigin` without `integrity` is allowed.

### 2. Nonce resolution (auto-detect)

A helper `resolve_nonce(context) -> str | None` (module-private to the templatetag layer),
first hit wins, **existence checks + `str()` force-evaluation, never truthiness**:

1. **Request attribute**: `getattr(request, crud_views_settings.csp_nonce_attr, None)` —
   covers django-csp on 4.2/5.2 and custom middleware. `request` comes from the tag context
   (requires the standard `request` context processor; absent request is tolerated).
2. **Django 6 built-in**: `from django.middleware.csp import get_nonce` inside
   `try/except ImportError` (module exists only on 6.0+); use `get_nonce(request)`.
3. **Context variable**: `context.get("csp_nonce")` — covers Django 6's `csp` context
   processor and hand-rolled setups without a request in context.

Resolved values are passed through `str()`; empty results are treated as no nonce.
No hit → rendered output is byte-identical to today.

Rationale for force-evaluation (vs. Django's passive `{% if csp_nonce %}` pattern): if the
project configured a nonce source in its policy, omitting `nonce` attributes would block
every registry-rendered script; if it didn't, a generated-but-unused nonce is dropped from
the header by `build_policy()`. Middleware presence signals intent.

### 3. Template tags and templates

- `cv_js` / `cv_css` (already `takes_context=True`) add `nonce` to the inclusion-tag context
  and extend each item dict: `{"url", "integrity", "crossorigin"}`.
- `shared/js.html`:
  `<script type="application/javascript" src="…"[ nonce="…"][ integrity="…" crossorigin="…"]></script>`
- `shared/css.html`:
  `<link rel="stylesheet" href="…"[ nonce="…"][ integrity="…" crossorigin="…"]>`
- Attributes render conditionally; all values are auto-escaped template variables.

### 4. Settings

One new field on `CrudViewsSettings`:

- `csp_nonce_attr: str = "csp_nonce"` → `CRUD_VIEWS_CSP_NONCE_ATTR`. Only needed for
  non-standard middleware that stores the nonce under a different request attribute.

### 5. System checks

Extend `crud_views/checks.py` (existing IDs end at W321):

- **`crud_views.E330`**: `Asset.integrity` set but not prefixed `sha256-`/`sha384-`/`sha512-`.
- **`crud_views.W331`**: `Asset.integrity` set on a non-external (same-origin static) path —
  SRI on own static files breaks on every asset edit and adds no security value.

### 6. Out of scope

- Emitting CSP headers or policy configuration (the project's middleware owns that).
- Auto-computing SRI hashes for local files.
- Arbitrary attribute pass-through (`defer`, `type="module"`, …) — the `Asset` dataclass
  leaves room to add fields later without another format change.
- Non-registry assets (e.g. example-project base templates linking CDNs directly).

## Testing

- **Unit**: string→`Asset` normalization, duplicate-key behavior unchanged, `resolve_nonce`
  precedence (attr beats Django 6 helper beats context var), empty/missing request handling,
  both new system checks.
- **Rendering (all matrix versions)**: no nonce → byte-identical output; fake
  `request.csp_nonce` as a plain string (django-csp path, no new dependency); SRI entry
  renders `integrity` + default `crossorigin="anonymous"`.
- **Django 6 end-to-end** (version-gated with `skipif`): real
  `ContentSecurityPolicyMiddleware` + `SECURE_CSP` containing `CSP.NONCE`; assert the nonce
  in the rendered tags matches the `Content-Security-Policy` response header, exercising the
  `LazyNonce` round-trip.

## Documentation

- `docs/reference/settings.md` CSP section: replace "No nonces or hashes are required" with
  the new story — host-allowlist CSP works with zero config; strict nonce-based CSP is
  auto-detected (django-csp and Django 6 built-in); SRI example using `Asset`.
- Document `CRUD_VIEWS_CSP_NONCE_ATTR` in the settings table.
- Changelog entry; follow-up: update the plugin SKILL.md in the skills monorepo after release.
