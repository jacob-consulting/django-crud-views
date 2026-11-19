# Direct source evidence for R17–R19 closure

These are bounded direct source reads, separate from the effective intel adapter verdict. They substantiate how the revised task text addresses the prior findings; no new implementation is asserted.

## src/crud_views/lib/view/context.py

9: class ViewContext(BaseModel, arbitrary_types_allowed=True):
10:     """
11:     A container that is passed to methods of CrudView with the context:
12:         - views
13:         - object
14:     """
15: 
16:     view: "CrudView"
17:     # typed Any (not Model | Resource) to avoid a module-level import of
18:     # crud_views.lib.resource here: resource.py imports
19:     # crud_views.lib.viewset.path_regs, which forces crud_views.lib.viewset's
20:     # __init__ to run, which itself imports crud_views.lib.resource — whichever
21:     # of {this module, viewset/__init__} runs first wins and the other sees a
22:     # partially-initialized module. Deferring the isinstance check below to
23:     # call-time (well after all modules have finished importing) sidesteps the
24:     # cycle entirely; see validate_object.
25:     object: Any = None
26: 
27:     @field_validator("object", mode="before")
28:     @classmethod
29:     def validate_object(cls, value: Any) -> Any:
30:         """
31:         When passed from template, an empty string is passed as object.
32:         """
33:         if value == "":
34:             return None
35:         if value is not None:
36:             from django.db.models import Model
37: 
38:             from crud_views.lib.resource import Resource
39: 
40:             if not isinstance(value, (Model, Resource)):
41:                 raise ValueError(f"ViewContext.object must be a Model or Resource instance, got {type(value)!r}")
42:         return value
43: 
44:     def to_dict(self) -> dict[str, Any]:
45:         return {"object": self.object}

## src/crud_views/lib/view/base.py

637:     @classmethod
638:     def cv_get_action_short_label(cls, context: ViewContext) -> str:
639:         return cls.render_snippet(
640:             cls.cv_viewset.get_meta(context),
641:             cls.cv_action_short_label_template,
642:             cls.cv_action_short_label_template_code,
643:         )

## src/crud_views/lib/viewset/__init__.py

78:     pk: str | None = None  # auto-detected from model if not set
79:     pk_name: str = "pk"
80:     context_buttons: list[ContextButton] = Field(default_factory=context_buttons_default)

## src/crud_views/lib/viewset/__init__.py

530:             "verbose_name": capfirst(verbose_name),
531:             "verbose_name_plural": capfirst(verbose_name_plural),
532:         }
533:         data.update(
534:             {
535:                 "verbose_name_translate": _(data["verbose_name"]),
536:                 "verbose_name_plural_translate": _(data["verbose_name_plural"]),
537:             }
538:         )
539:         data.update(context.to_dict())
540:         return data

## tests/test1/test_guardian_child_link_visibility.py

1052: def reset_discovery(links):
1053:     from django.contrib.contenttypes.models import ContentType
1054:     from guardian.shortcuts import clear_ct_cache
1055: 
1056:     ContentType.objects.clear_cache()
1057:     clear_ct_cache()
1058:     links.parent._default_permissions = None
1059:     links.child._default_permissions = None

## src/crud_views/lib/viewset/__init__.py

223: 
224:     @staticmethod
225:     def checks_all() -> Iterable[Check]:
226:         """
227:         Iterator over all checks of all viewsets
228:         """
229:         with _REGISTRY_LOCK:
230:             viewsets = list(_REGISTRY.values())
231:         for cv in viewsets:
232:             yield from cv.checks()

## src/crud_views/lib/viewset/__init__.py

283:                 ),
284:             )
285: 
286:         for view in self._views.values():
287:             yield from view.checks()

## src/crud_views/checks.py

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

## src/crud_views/checks.py

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

## src/crud_views/lib/view/base.py

578:     def render_snippet(cls, data: dict, template: str | None = None, template_code: str | None = None) -> str:
579:         """
580:         Either render the template_code or the template
581:         """
582:         if template_code:
583:             template = Template(template_code)
584:             context = TemplateContext(data)
585:             result = template.render(context)
586:         elif template:
587:             result = render_to_string(template, data)
588:         else:
589:             raise CrudViewError(f"no template or template_code provided for {cls}")
590: 
591:         # strip leading and trailing whitespaces and mark it as safe
592:         return mark_safe(result.strip())
