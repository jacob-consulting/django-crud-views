from collections import defaultdict
from typing import NamedTuple

from django.contrib.admin.utils import NestedObjects
from django.db import router
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.views.mixins import CrudViewProcessFormMixin


class RelatedObjects(NamedTuple):
    tree: list
    summary: dict[str, int]
    protected: list


class DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView):
    template_name = "crud_views/view_delete.html"

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
        if self.cv_show_related_objects:
            related = self.cv_get_related_objects()
            related = self.cv_filter_related_objects(self.request.user, related)
            context["related_objects"] = related.tree
            context["related_summary"] = related.summary
            context["protected_objects"] = related.protected
        return context

    def cv_check_delete_protection(self) -> list[str]:
        return []

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except AttributeError:
            self.object = None

        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            errors = self.cv_check_delete_protection()
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
