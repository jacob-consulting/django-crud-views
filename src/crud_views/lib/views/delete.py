import logging
from collections import defaultdict
from typing import NamedTuple

from django.contrib.admin.utils import NestedObjects
from django.db import router
from django.urls import NoReverseMatch, reverse
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.views.mixins import CrudViewProcessFormMixin

logger = logging.getLogger(__name__)


class RelatedObjects(NamedTuple):
    tree: list
    summary: dict[str, int]
    protected: list


class DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView):
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
    cv_icon_action = "fa-regular fa-trash-can"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/delete.html"

    def cv_get_related_objects(self) -> RelatedObjects:
        using = router.db_for_write(self.object._meta.model)
        collector = NestedObjects(using=using)
        collector.collect([self.object])

        summary = defaultdict(int)
        for model, instances in collector.data.items():
            if model == self.object._meta.model:
                continue
            summary[model._meta.verbose_name] += len(instances)

        tree = collector.nested()

        return RelatedObjects(tree=tree, summary=dict(summary), protected=list(collector.protected))

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
        return RelatedObjects(tree=filtered_tree, summary=related.summary, protected=related.protected)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        errors = self.cv_check_delete_protection()
        if errors:
            context["delete_protection_errors"] = errors
        if self.cv_show_related_objects:
            related = self.cv_get_related_objects()
            related = self.cv_filter_related_objects(self.request.user, related)
            context["related_summary"] = related.summary
            context["protected_objects"] = related.protected

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
        self.object = self.get_object()

        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            # get_context_data already ran the delete protection check
            errors = context.get("delete_protection_errors", [])
            if errors:
                form = context["form"]
                for error in errors:
                    form.add_error(None, error)
                return self.render_to_response(context)
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            return self.cv_form_valid_redirect(context)
        else:
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)

    def cv_form_valid(self, context: dict):
        self.object.delete()


class DeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, DeleteView):
    cv_permission = "delete"
