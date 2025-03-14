from typing import List, Tuple

from black.nodes import parent_type
from django.urls.base import reverse

from crud_views.lib.viewset import ViewSet

TBreadCrumbInfo = Tuple[str, str | None, tuple | None, str]
TBreadCrumbInfoList = List[TBreadCrumbInfo]


class MenuMixin:

    # this is global for all views and viewsets
    # todo: maybe we should move it to the ParentViewset class ?
    cv_bc_key_container: str = "list"
    cv_bc_key_object: str = "detail"

    def cv_bc_get(self) -> TBreadCrumbInfoList:
        """
        Get breadcrumb items for this viewset
        """

        # result items
        bc: TBreadCrumbInfoList = []

        obj = getattr(self, "object", None)
        context = self.cv_get_view_context(object=obj)

        # local helpers
        def verbose_name_plural(viewset: ViewSet) -> str:
            return viewset.get_meta(context)["verbose_name_plural_translate"]

        # 1. if view is object then add
        #   - object action label, no link
        #   - object name, link to page
        #   - parent action label, link to list (if present)
        # 2. else
        #   - if key is not list then add action label, no link
        #   - get viewset name as list

        # 1.
        if self.cv_object:
            # object action label, no link
            bc.append((self.cv_get_action_short_label(context=context), None, None, None))

            # object name, link to page
            parent_router_name, args, kwargs = self.cv_get_router_and_args(self.cv_key, obj=obj)
            bc.append((str(self.object), parent_router_name, args, reverse(parent_router_name, args=args)))

            # parent action label, link to list (if present)
            parent_router_name, args, kwargs = self.cv_get_router_and_args(self.cv_bc_key_container, obj=obj)
            list_label = verbose_name_plural(self.cv_viewset)
            bc.append((list_label, parent_router_name, args, reverse(parent_router_name, args=args)))

        # 2.
        else:
            # if key is not list then add action label, no link
            if self.cv_key != "list":
                bc.append((self.cv_get_action_short_label(context=context), None, None, None))

            # get viewset name as list
            parent_router_name, args, kwargs = self.cv_get_router_and_args(self.cv_bc_key_container, obj=obj)
            list_label = verbose_name_plural(self.cv_viewset)
            bc.append((list_label, parent_router_name, args, reverse(parent_router_name, args=args)))

        # get parents (in reverse order)
        parents = []
        if self.cv_viewset.parent:
            parent = self.cv_viewset.parent
            while parent is not None:
                parents.append(parent)
                parent = parent.viewset.parent

        # get current router and args
        parent_router_name, args, kwargs = self.cv_get_router_and_args(self.cv_key, obj=obj)

        # get parent args, args names
        parent_arg_values = args[:-1] if self.cv_object else args
        parent_arg_names = self.cv_viewset.get_parent_url_args()
        parent_arg_names.reverse()
        assert len(parents) == len(parent_arg_values) == len(parent_arg_names)

        y = 1

        # process parents from bottom to top
        for i, parent in enumerate(parents):
            x = len(parents) - i
            arg_names = parent_arg_names[:x]
            arg_values = parent_arg_values[:x]
            arg_names[-1] = parent.viewset.pk_name

            # add linking parent object
            parent_pk = arg_values[-1]
            parent_object = parent.viewset.get_queryset(view=self).get(pk=parent_pk)
            parent_router_name = parent.viewset.get_router_name(key=self.cv_bc_key_object)
            url = reverse(parent_router_name, args=arg_values)
            bc.append((str(parent_object), parent_router_name, arg_values, url))

            # get container: list view
            base_label = verbose_name_plural(parent.viewset)
            base_router_name = parent.viewset.get_router_name(key=self.cv_bc_key_container)
            base_args_values = arg_values[:-1]
            base_url = reverse(base_router_name, args=base_args_values)
            bc.append((base_label, base_router_name, base_args_values, base_url))
            x = 1

        bc.reverse()
        return bc

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bc: TBreadCrumbInfoList = self.cv_bc_get()
        context["bc"] = bc
        return context
