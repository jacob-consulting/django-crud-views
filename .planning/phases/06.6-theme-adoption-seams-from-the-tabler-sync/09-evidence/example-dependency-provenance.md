# Example gate dependency

The required example suite failed collection because `django_ratelimit` was absent from the cached
Django 5.2 environment. `requirements/demo.txt` already declares `django-ratelimit>=4.1`.
The existing user authorization covers necessary environment setup; no package substitution was made.

Official [PyPI metadata](https://pypi.org/pypi/django-ratelimit/json) identifies James Socol's
[django-ratelimit repository](https://github.com/jsocol/django-ratelimit) and maintained Django rate-limit
package. Metadata was checked before running the install. The exact resolved version was **4.1.0**.

Command: `uv pip install --python .nox/tests-3-12-django-5-2/bin/python 'django-ratelimit>=4.1'`.
The retained `example-dependency-install.log` records one resolved/installed package and no changed dependency
versions. `example-regression.log` records 45 passing docs-sync/rate-limit tests after installation and the
stale parent-helper documentation repair. The full example gate separately passes 301 tests.

No production dependency manifest, lock file, package name, companion environment or floor pin was changed.
The original failed collection and stale-doc assertion remain embedded in `prior-gates.json`.
