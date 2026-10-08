# Asset registry

Any Django app can contribute JavaScript and CSS to the output of `{% cv_js %}` and
`{% cv_css %}` by registering an asset bundle in its `AppConfig.ready()`:

```python
# myextension/apps.py
from django.apps import AppConfig


class MyExtensionConfig(AppConfig):
    name = "myextension"

    def ready(self):
        from crud_views.lib.assets import register_assets

        register_assets(
            key="myextension",
            js=["myextension/plugin.js", "myextension/init.js"],
            css=["myextension/plugin.css"],
        )
```

Rules:

- Entries are static paths resolved through `{% static %}` — unless they start with
  `http://`, `https://` or `//`, in which case they are rendered verbatim (CDN mode).
- Entries may also be `Asset` instances (`crud_views.lib.assets.Asset`) carrying `integrity`/
  `crossorigin` SRI metadata for external URLs — see
  [Subresource integrity (SRI)](settings.md#subresource-integrity-sri) in the settings
  reference. `{% cv_js %}`/`{% cv_css %}` also auto-detect a CSP nonce; see
  [Nonce support](settings.md#nonce-support).
- Core assets always render first; registered bundles follow in registration order,
  which equals `INSTALLED_APPS` order.
- `key` must be unique; registering the same key twice raises `ImproperlyConfigured`.
- `register_assets(..., emit=False)` keeps the bundle registered but excludes it from
  tag output. To deliver crud-views assets through django-pipeline, prefer
  [bundled mode](#bundling-with-django-pipeline), which covers core and every bundle at once.
  Vendored bundles are validated separately via `check_vendored()`, which an
  extension app wires into its own system checks; it is not run automatically.
- The key `crud_views` is reserved for the package's own assets.
- jQuery is **not** managed by the registry. As with core's own scripts, the project
  loads jQuery in its base template before `{% cv_js %}`.

## Vendoring third-party files

`crud_views.lib.vendor` provides shared infrastructure for extension apps that offer a
"download the pinned version locally" management command:

```python
from crud_views.lib.vendor import VendorSpec, vendor, check_vendored

spec = VendorSpec(
    key="myextension",
    version="1.2.3",
    base_url="https://cdn.jsdelivr.net/npm/some-pkg@{version}/dist/",
    files=("plugin.js", "plugin.css"),
    target=vendor_dir / "myextension" / "1.2.3",
)
vendor(spec)  # downloads files + writes a version stamp
check_vendored(spec)  # system-check messages on drift (W330 missing, W331 mismatch)
```

The target must be a project directory that is on `STATICFILES_DIRS` — never a
directory inside an installed package.

## Bundling with django-pipeline

Projects using [django-pipeline](https://django-pipeline.readthedocs.io/) can put every *local*
crud-views asset — core and all registered bundles — into their pipeline packages without listing
files by hand:

```python
# settings.py
from crud_views.lib.pipeline import cv_sources

CRUD_VIEWS_ASSETS_BUNDLED = True  # {% cv_js %}/{% cv_css %} now emit only CDN entries

PIPELINE = {
    "JAVASCRIPT": {
        "main": {
            "source_filenames": cv_sources("js", before=["js/jquery.js"], after=["js/app.js"]),
            "output_filename": "js/main.js",
        },
    },
    "STYLESHEETS": {
        "main": {
            "source_filenames": cv_sources("css", after=["css/app.css"]),
            "output_filename": "css/main.css",
        },
    },
}
```

`cv_sources()` returns a lazy list: django-pipeline reads it when a package is rendered or
collected, after every app has registered its assets. Adding or removing an extension app needs no
settings change. Order: `before`, core assets, registered bundles (`INSTALLED_APPS` order), `after`.

!!! warning "Do not expand it in settings.py"
    `[*cv_sources("js")]` or `list(cv_sources("js"))` resolves too early and raises
    `AppRegistryNotReady`. Put extra files into `before=`/`after=`, or combine with `+`:
    `["js/jquery.js"] + cv_sources("js")` stays lazy.

Arguments:

| Argument | Meaning |
|---|---|
| `kind` | `"js"` or `"css"` |
| `before` / `after` | static paths placed around the registry entries (e.g. jQuery, which the registry does not manage) |
| `keys` | only these bundle keys (`"crud_views"` = core); `None` = all, `[]` = none |
| `exclude` | drop these bundle keys |

Split across packages by calling it more than once, e.g.
`cv_sources("js", exclude=["datetimepicker"])` in `"main"` and
`cv_sources("js", keys=["datetimepicker"])` in `"forms"`.

### What can and cannot be bundled

- Pipeline only concatenates files on disk; **CDN entries cannot be bundled**. `cv_sources()`
  leaves them out and `{% cv_js %}`/`{% cv_css %}` keep rendering them (with SRI and nonce) — keep
  the tags in your base template.
- **Core has no CDN entries**: with only core installed, bundled mode makes both tags render nothing.
- **Extensions must be in a local (vendored) mode to be fully bundled.** An extension in CDN mode
  would get its local init script bundled while its plugin stays a CDN tag (check W345).
  For `crud_views_widget_datetimepicker`: `SOURCE="vendored"` plus `manage.py cv_vendor_datetimepicker`.
- Re-minifying already-minified vendor files with pipeline's compressors is harmless.
- Template order in bundled mode: project CDN dependencies (Bootstrap, jQuery) →
  `{% cv_css %}{% cv_js %}` → `{% stylesheet "main" %}{% javascript "main" %}`.

### Listing assets: `cv_assets`

```
$ python manage.py cv_assets
KEY             KIND  DELIVERY        PATH
crud_views      js    pipeline:main   crud_views/js/viewset.js
...
datetimepicker  js    tag (CDN)       https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.full.min.js
datetimepicker  js    pipeline:main   crud_views_widget_datetimepicker/init.js
```

Delivery is `tag`, `tag (CDN)`, `pipeline:<package>`, `none` (delivered by nothing) or
`none (emit=False)`. Options: `--external` (only CDN entries — the list to vendor for production),
`--kind js|css`, `--format table|json`. The JSON output also gives you the CDN hosts for a CSP
`script-src`/`style-src` allowlist.

### Checks

| ID | Meaning |
|---|---|
| `crud_views.W340` | Bundled mode is on, but no `PIPELINE` package uses `cv_sources()`. |
| `crud_views.W341` | Bundled mode: a local asset is in no pipeline package of its kind. |
| `crud_views.W342` | Not bundled, but `cv_sources()` bundles assets the tags also emit (double load). |
| `crud_views.W343` | `keys=`/`exclude=` names an unknown bundle key. |
| `crud_views.W344` | `cv_sources("css")` under `JAVASCRIPT` or vice versa. |
| `crud_views.W345` | Bundled mode: a bundle mixes CDN and local entries — vendor that extension. |

Plain string entries in `source_filenames` (including glob patterns) count as coverage too, so
hand-maintained lists get the same checks.
