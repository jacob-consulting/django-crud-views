# Supplemental source reads — cycle 4

These direct reads support R20 mechanism review. They do not replace the effective intel authority; Python/signature adapter verdicts remain UNCHECKABLE. This is planning review, not evidence that the proposed edits or tests have executed.

## src/crud_views/checks.py:38
```text
38: @register(TAG)
39: def check_viewsets(app_configs=None, **kwargs):
40:     """Run all ViewSet, CrudView and settings checks."""
41: 
42:     errors = crud_views_settings.check_messages
43: 
44:     for check in ViewSet.checks_all():
45:         for message in check.messages():
46:             errors.append(message)
47:     return errors
```

## src/crud_views/checks.py:172
```text
172: def _url_configuration_loaded() -> bool:
173:     """The readiness barrier of the completion-dependent ancestor checks.
174: 
175:     Import the configured ROOT_URLCONF and every included URLconf through Django's own resolver (visiting each
176:     resolver once), so view modules that only the URLconf imports have registered their views. True when that
177:     completed; False without ROOT_URLCONF, or when the import failed or is still in progress (a check run
178:     during URLconf import) — Django's own URL checks report such failures. Nothing is remembered between calls.
179:     """
180:     from django.conf import settings
181:     from django.urls import URLResolver, get_resolver
182: 
183:     if not getattr(settings, "ROOT_URLCONF", None):
184:         return False
185:     pending, seen = [get_resolver()], set()
186:     try:
187:         while pending:
188:             resolver = pending.pop()
189:             if id(resolver) in seen:
190:                 continue
191:             seen.add(id(resolver))
192:             pending.extend(pattern for pattern in resolver.url_patterns if isinstance(pattern, URLResolver))
193:     except Exception:  # any import failure means "not completed", never a misleading missing-action error
194:         return False
195:     return True
196: 
197: 
198: @register(TAG)
199: def check_ancestor_declarations(app_configs=None, **kwargs):
200:     """Ancestor structure and action declarations of every registered nested ViewSet (phase 06.18).
201: 
202:     Cycles and unsupported relationships are always reported. Unregistered parents, unregistered action keys
203:     and missing custom-endpoint entries depend on a completed registry: they are checked only after the
204:     configured URLconf (and everything it includes) has been imported; otherwise they are deferred. Runtime
205:     guards enforce all of them on the actual request regardless.
206:     Undeclared ``cv_permission`` and ancestor pair keys (viewset.E269) are checked against the
207:     respective model's declared permissions in the same completed-registry pass.
208:     """
209:     completed = _url_configuration_loaded()
210:     with _REGISTRY_LOCK:
211:         viewsets = list(_REGISTRY.values())
212:     return collect_ancestor_checks(viewsets, completed=completed)
213: 
```

## src/crud_views/lib/viewset/__init__.py:224
```text
224:     @staticmethod
225:     def checks_all() -> Iterable[Check]:
226:         """
227:         Iterator over all checks of all viewsets
228:         """
229:         with _REGISTRY_LOCK:
230:             viewsets = list(_REGISTRY.values())
231:         for cv in viewsets:
232:             yield from cv.checks()
```

## src/crud_views/lib/viewset/__init__.py:286
```text
286:         for view in self._views.values():
287:             yield from view.checks()
```

## .nox/tests-3-12-django-5-2/lib/python3.12/site-packages/django/urls/resolvers.py:708
```text
708:     @cached_property
709:     def urlconf_module(self):
710:         if isinstance(self.urlconf_name, str):
711:             return import_module(self.urlconf_name)
712:         else:
713:             return self.urlconf_name
714: 
715:     @cached_property
716:     def url_patterns(self):
717:         # urlconf_module might be a valid set of patterns, so we default to it
718:         patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)
719:         try:
720:             iter(patterns)
721:         except TypeError as e:
722:             msg = (
723:                 "The included URLconf '{name}' does not appear to have "
724:                 "any patterns in it. If you see the 'urlpatterns' variable "
725:                 "with valid patterns in the file then the issue is probably "
726:                 "caused by a circular import."
727:             )
728:             raise ImproperlyConfigured(msg.format(name=self.urlconf_name)) from e
729:         return patterns
730: 
```

## .nox/tests-3-12-django-5-2/lib/python3.12/site-packages/django/utils/functional.py:39
```text
39:     def __get__(self, instance, cls=None):
40:         """
41:         Call the function and put the return value in instance.__dict__ so that
42:         subsequent attribute access on the instance returns the cached value
43:         instead of calling cached_property.__get__().
44:         """
45:         if instance is None:
46:             return self
47:         res = instance.__dict__[self.name] = self.func(instance)
48:         return res
```

## R20 current plan obligation
PLAN01 Task03 now orders URLconf completion before checks_all begins. The navbar cooperative hook may only read cached url_patterns in load=False mode; missing cached properties defer registry-dependent errors without import retries. Tests must assert every distinct late diagnostic, including new ViewSets, failed preflight and later completion.

## Supported Django cached-property source inspection
- `.nox/tests-3-12-django-4-2/lib/python3.12/site-packages/django/urls/resolvers.py:713`: `def url_patterns(self):`
- `.nox/tests-3-12-django-4-2/lib/python3.12/site-packages/django/utils/functional.py:57`: `res = instance.__dict__[self.name] = self.func(instance)`
- `.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/django/urls/resolvers.py:716`: `def url_patterns(self):`
- `.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/django/utils/functional.py:47`: `res = instance.__dict__[self.name] = self.func(instance)`
- `.nox/tests-3-12-django-6-0/lib/python3.12/site-packages/django/urls/resolvers.py:727`: `def url_patterns(self):`
- `.nox/tests-3-12-django-6-0/lib/python3.12/site-packages/django/utils/functional.py:47`: `res = instance.__dict__[self.name] = self.func(instance)`

## tests/test1/test_ancestor_authorization.py:46
```text
46: @contextmanager
47: def isolated_routes(build):
48:     """Run ``build(sfx)`` (which constructs ViewSets/views and returns ``(namespace, viewsets_to_route)``) behind
49:     a temporary ROOT_URLCONF; restore registry, vocabulary cache, URL caches and ContentType cache afterwards."""
50:     sfx = uuid.uuid4().hex[:8]
51:     modname = f"tests.test1._ancestor_urls_{sfx}"
52:     with _REGISTRY_LOCK:
53:         registry_snapshot = dict(_REGISTRY)
54:     vocab_snapshot = dict(check_module._VOCAB_CACHE)
55:     try:
56:         namespace, routed = build(sfx)
57:         module = types.ModuleType(modname)
58:         module.urlpatterns = [pattern for vs in routed for pattern in vs.urlpatterns]
59:         module.urlpatterns.append(path("", include("tests.test1.project.urls")))
60:         sys.modules[modname] = module
61:         clear_url_caches()
62:         with override_settings(ROOT_URLCONF=modname):
63:             clear_url_caches()
64:             try:
65:                 yield namespace
66:             finally:
67:                 clear_url_caches()
68:     finally:
69:         with _REGISTRY_LOCK:
70:             _REGISTRY.clear()
71:             _REGISTRY.update(registry_snapshot)
72:         check_module._VOCAB_CACHE.clear()
73:         check_module._VOCAB_CACHE.update(vocab_snapshot)
74:         sys.modules.pop(modname, None)
75:         clear_url_caches()
76:         ContentType.objects.clear_cache()
77: 
78: 
79: def _url(vs: ViewSet, key: str, **kwargs) -> str:
```

## src/crud_views/lib/viewset/__init__.py:352
```text
352:     def register_view_class(self, key: str, view_class: type[CrudView]):
353:         cv_raise(key not in self._views, f"key {key} already registered at {self}")
354:         self._views[key] = view_class
```
