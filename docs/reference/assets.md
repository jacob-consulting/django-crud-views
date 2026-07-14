# Asset registry

Any Django app can contribute JavaScript and CSS to the output of `{% cv_js %}` and
`{% cv_css %}` by registering an asset bundle in its `AppConfig.ready()`:

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

Rules:

- Entries are static paths resolved through `{% static %}` — unless they start with
  `http://`, `https://` or `//`, in which case they are rendered verbatim (CDN mode).
- Core assets always render first; registered bundles follow in registration order,
  which equals `INSTALLED_APPS` order.
- `key` must be unique; registering the same key twice raises `ImproperlyConfigured`.
- `register_assets(..., emit=False)` keeps the bundle registered (its system checks
  still run) but excludes it from tag output — use this when a bundler such as
  django-pipeline delivers the files instead.
- jQuery is **not** managed by the registry. As with core's own scripts, the project
  loads jQuery in its base template before `{% cv_js %}`.

## Vendoring third-party files

`crud_views.lib.vendor` provides shared infrastructure for extension apps that offer a
"download the pinned version locally" management command:

    from crud_views.lib.vendor import VendorSpec, vendor, check_vendored

    spec = VendorSpec(
        key="myextension",
        version="1.2.3",
        base_url="https://cdn.jsdelivr.net/npm/some-pkg@{version}/dist/",
        files=("plugin.js", "plugin.css"),
        target=vendor_dir / "myextension" / "1.2.3",
    )
    vendor(spec)            # downloads files + writes a version stamp
    check_vendored(spec)    # system-check messages on drift (W330 missing, W331 mismatch)

The target must be a project directory that is on `STATICFILES_DIRS` — never a
directory inside an installed package.
