# Example management commands

Run these commands from `examples/bootstrap5` with the project's virtual environment activated.
The examples assume the database has been migrated and seeded with `alice`, `bob`, and `developer`.

```bash
# Explain Alice's access to the author list
python manage.py cv_access /library/author/ alice

# Compare create permissions: Alice versus read-only developer
python manage.py cv_access /library/author/create/ alice
python manage.py cv_access /library/author/create/ developer

# Check anonymous access
python manage.py cv_access /library/author/ --anonymous

# Get a machine-readable trace
python manage.py cv_access /library/author/ alice --as-json --no-color

# Compare the restricted ticket scenario
python manage.py cv_access /context-buttons/ticket/create/ alice
python manage.py cv_access /context-buttons/ticket/create/ bob

# Ensure the developer diagnostics group exists
python manage.py cv_manage_group

# Inspect registered assets
python manage.py cv_assets
python manage.py cv_assets --external
python manage.py cv_assets --kind css --format json
```

`cv_manage_group` only creates the configured group; it does not assign users or permissions.
