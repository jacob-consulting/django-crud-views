import logging
from collections.abc import Iterable
from contextlib import nullcontext
from functools import partial
from typing import ClassVar

from django.core.exceptions import ImproperlyConfigured
from django.db import connections, router, transaction
from django.db.models import Model
from django.urls import NoReverseMatch, reverse
from django.views import generic

from crud_views.lib.check import Check, CheckExpression
from crud_views.lib.deletion import (
    RelatedObjects,
    _NativeDeleteBlocked,
    execute_deletion,
    inspect_deletion,
    merge_delete_preview,
)
from crud_views.lib.exceptions import ViewSetKeyFoundError
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.view.base import cv_is_modal_request
from crud_views.lib.views.mixins import CrudViewProcessFormMixin

logger = logging.getLogger(__name__)


class _DeleteMethodGuardMixin:
    """Reject HTTP DELETE on every package delete view; deletion only runs through the validated POST.

    Sits after ``CrudView`` and before Django's ``DeleteView`` in the MRO: authentication, permission and parent
    gates (``PermissionRequiredMixin``, Guardian's parent mixin) run first, ``CrudView.dispatch`` still adds the
    modal ``Vary`` header, and a subclass that puts ``"delete"`` back into ``http_method_names`` is still stopped
    here before any handler or object lookup. Django's inherited ``delete()`` is left untouched on purpose, so
    Django 4.2 emits no ``DeleteViewCustomDeleteWarning``.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.method == "DELETE":
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def _allowed_methods(self):
        # feeds both the 405 Allow header and OPTIONS, so neither advertises DELETE
        return [method for method in super()._allowed_methods() if method != "DELETE"]


class DeleteView(CrudViewProcessFormMixin, CrudView, _DeleteMethodGuardMixin, generic.DeleteView):
    http_method_names: ClassVar[list[str]] = [m for m in generic.DeleteView.http_method_names if m != "delete"]
    template_name = "crud_views/view_delete.html"
    cv_content_template = "crud_views/view_delete.content.html"
    cv_modal_supported = True

    cv_key = "delete"
    cv_path = "delete"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.delete_context_actions

    # related objects
    cv_show_related_objects: bool = False
    cv_link_related_objects: bool = False

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/delete.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/delete.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/delete.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/delete.html"

    # icons
    cv_icon_action = "delete"
    cv_action_variant = "danger"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/delete.html"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        yield CheckExpression(
            context=cls,
            id="E254",
            expression=not cls.cv_success_object_keys(),
            msg=(
                f"cv_success_key / cv_success_keys of a delete view must not be object views, the object is "
                f"gone after success, got {cls.cv_success_object_keys()!r}"
            ),
        )

    @classmethod
    def cv_success_object_keys(cls) -> list[str]:
        """Registered cv_success_key / cv_success_keys entries that need an object (unregistered ones are
        not this check's job)."""
        candidates = [*([cls.cv_success_key] if cls.cv_success_key else []), *(cls.cv_success_keys or [])]
        if not candidates or cls.cv_viewset is None:
            return []
        keys = []
        for key in candidates:
            try:
                if cls.cv_viewset.get_view_class(key).cv_object:
                    keys.append(key)
            except ViewSetKeyFoundError:
                pass
        return keys

    def cv_get_db_alias(self) -> str:
        return router.db_for_write(type(self.object), instance=self.object)

    def cv_get_delete_db_alias(self) -> str:
        """Pin the selection once, after authorized resolution of a saved target."""
        target = getattr(self, "object", None)
        if not isinstance(target, Model) or target._state.adding or target.pk is None:
            raise ImproperlyConfigured("Resolve a saved self.object before calling cv_get_delete_db_alias()")
        if not hasattr(self, "_cv_delete_db_alias"):
            using = self.cv_get_db_alias()
            if not isinstance(using, str) or not using or using not in connections:
                raise ImproperlyConfigured("cv_get_db_alias() must select a configured database alias")
            self._cv_delete_db_alias = using
        return self._cv_delete_db_alias

    def cv_get_atomic(self):
        using = self.cv_get_delete_db_alias()
        return transaction.atomic(using=using) if self.cv_atomic else nullcontext()

    def cv_form_valid_process(self, context: dict) -> None:
        using = self.cv_get_delete_db_alias()
        with self.cv_get_atomic():
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=using)

    def cv_get_delete_preview(self, boundaries, *, using):
        """Describe unknown effects using read-only DeletePreviewContribution records."""
        return ()

    def _cv_inspect_deletion(self):
        using = self.cv_get_delete_db_alias()
        if type(self).cv_get_related_objects is not DeleteView.cv_get_related_objects:
            raise ImproperlyConfigured(
                "cv_get_related_objects overrides are unsupported. Use cv_get_delete_preview() "
                "for read-only descriptions and cv_filter_related_objects() for display filtering."
            )
        if not hasattr(self, "_cv_delete_inspection"):
            inspection = inspect_deletion(self.object, using=using)
            contributions = self.cv_get_delete_preview(inspection.boundaries, using=using)
            self._cv_delete_inspection = merge_delete_preview(inspection, contributions, using=using)
        return self._cv_delete_inspection

    def cv_get_related_objects(self) -> RelatedObjects:
        """Read-only compatibility accessor; lifecycle overrides must use the safe provider."""
        return self._cv_inspect_deletion().related

    def cv_get_related_object_url(self, obj) -> str | None:
        from crud_views.lib.viewset import _REGISTRY

        model = type(obj)
        for viewset in _REGISTRY.values():
            if viewset.model == model and viewset.is_view_registered("detail"):
                try:
                    router_name = viewset.get_router_name("detail")
                    kwargs = {viewset.pk_name: obj.pk}
                    if viewset.parent:
                        parent_attr = viewset.parent.get_attribute()
                        parent_obj = getattr(obj, parent_attr, None)
                        if parent_obj:
                            kwargs[viewset.parent.get_pk_name()] = parent_obj.pk
                    return reverse(router_name, kwargs=kwargs)
                except NoReverseMatch:
                    logger.debug("cannot reverse detail url for %r at %s", obj, viewset, exc_info=True)
                    return None
        return None

    @staticmethod
    def _walk_nested(items):
        for item in items:
            if isinstance(item, (list, tuple)):
                yield from DeleteView._walk_nested(item)
            elif item is not None and hasattr(item, "_meta"):
                yield item

    def _build_display_tree(self, items, urls):
        result = []
        i = 0
        while i < len(items):
            item = items[i]
            if isinstance(item, (list, tuple)):
                # Nested list without preceding instance -- flatten
                result.extend(self._build_display_tree(item, urls))
                i += 1
            else:
                # Model instance or None
                children = []
                if i + 1 < len(items) and isinstance(items[i + 1], (list, tuple)):
                    children = self._build_display_tree(items[i + 1], urls)
                    i += 2
                else:
                    i += 1
                url = urls.get(id(item)) if item is not None else None
                result.append({"obj": item, "url": url, "children": children})
        return result

    def cv_filter_related_objects(self, user, related: RelatedObjects) -> RelatedObjects:
        permission_cache = {}

        def _has_view_permission(model):
            if model not in permission_cache:
                opts = model._meta
                perm = f"{opts.app_label}.view_{opts.model_name}"
                permission_cache[model] = user.has_perm(perm)
            return permission_cache[model]

        def _filter_tree(items):
            result = []
            for item in items:
                if isinstance(item, list):
                    result.append(_filter_tree(item))
                elif item is not None and hasattr(item, "_meta"):
                    if _has_view_permission(item._meta.model):
                        result.append(item)
                    else:
                        result.append(None)
                else:
                    result.append(item)
            return result

        filtered_tree = _filter_tree(related.tree)
        # only labels the user may view; the blocked state itself is captured before this hook runs
        protected = [obj for obj in related.protected if _has_view_permission(obj._meta.model)]
        return RelatedObjects(tree=filtered_tree, summary=related.summary, protected=protected)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        errors = self.cv_check_delete_protection()
        if errors:
            context["delete_protection_errors"] = errors
        inspection = self._cv_inspect_deletion()
        related = inspection.related
        context["delete_preview_incomplete"] = not inspection.complete
        # Only the boolean crosses the context boundary when the preview is disabled.
        context["has_protected_objects"] = bool(related.protected)
        if self.cv_show_related_objects:
            related = self.cv_filter_related_objects(self.request.user, related)
            context["related_summary"] = related.summary
            context["related_summary_items"] = [f"{name}: {count}" for name, count in related.summary.items()]
            context["protected_objects"] = list(related.protected)

            urls = {}
            if self.cv_link_related_objects:
                for obj in self._walk_nested(related.tree):
                    url = self.cv_get_related_object_url(obj)
                    if url:
                        urls[id(obj)] = url

            context["related_objects"] = self._build_display_tree(related.tree, urls)
        return context

    def cv_check_delete_protection(self) -> list[str]:
        return []

    def post(self, request, *args, **kwargs):
        """Honor preview protection; translate only the private pre-write marker after atomic unwind.

        Lifecycle, custom relationship/default/loading and commit-callback failures retain propagation and
        cv_atomic semantics. A failed callback must never report an already committed deletion as blocked.
        """
        self.object = self.get_object()

        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            # get_context_data already ran the delete protection check
            errors = context.get("delete_protection_errors", [])
            if errors or context["has_protected_objects"]:
                form = context["form"]
                for error in errors:
                    form.add_error(None, error)
                return self._cv_protection_response(context)
            try:
                self.cv_form_valid_process(context)
            except _NativeDeleteBlocked:
                context["has_protected_objects"] = True
                return self._cv_protection_response(context)
            return self.cv_form_valid_redirect(context)
        else:
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)

    def _cv_protection_response(self, context):
        response = self.render_to_response(context)
        if self.cv_modal and cv_is_modal_request(self.request):
            response.status_code = 422
        return response

    def cv_form_valid(self, context: dict):
        execute_deletion(self.object, using=self.cv_get_delete_db_alias())


class DeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, DeleteView):
    cv_permission = "delete"
