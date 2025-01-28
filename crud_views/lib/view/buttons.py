from django.contrib.auth import get_user_model
from django.urls import reverse
from pydantic import BaseModel

from .context import ViewContext
from ..settings import crud_views_settings
from ..exceptions import ViewSetViewError

User = get_user_model()


class ContextButton(BaseModel):
    """
    A context button is a button that is rendered in the context of a ViewSetView
    """
    key: str
    key_target: str
    label_template: str | None = None
    label_template_code: str | None = None

    def render_label(self, data: dict, context: ViewContext) -> str:
        if self.label_template:
            return context.view.render_snippet(data, self.label_template)
        elif self.label_template_code:
            return context.render_snippet(data, template_code=self.label_template_code)

    def get_context(self, context: ViewContext) -> dict:

        dict_kwargs = dict(
            vs_access=False,
            vs_url=context.view.vs_get_url(key=self.key_target, obj=context.object)
        )

        # get target view class
        cls = context.view.vs_get_cls_assert_object(self.key_target, context.object)

        # check access
        if cls.vs_has_access(context.view.request.user, context.object):
            # get the url for the target key
            dict_kwargs.update(
                vs_access=True,
            )

        # final data
        data = cls.vs_get_dict(context=context, **dict_kwargs)

        # render action label
        vs_action_label = self.render_label(data, context)
        if vs_action_label:
            data["vs_action_label"] = vs_action_label

        return data


class ParentContextButton(ContextButton):
    """
    A context button that
    """

    def get_context(self, context: ViewContext) -> dict:

        # does the view has no parent?
        if not context.view.vs.parent:
            return dict()

        # get parent view class, defined by target
        parent = context.view.vs.parent
        cls = parent.viewset.get_view_class(self.key_target)

        dict_kwargs = dict(
            vs_access=False,
            vs_icon_action=cls.vs.icon_header
        )

        # parent url kwargs
        kwargs = dict()
        for idx, arg in enumerate(context.view.vs.get_parent_url_args()):
            if idx == 0:
                if cls.vs_object:
                    kwargs[parent.viewset.pk_name] = context.view.kwargs[arg]
            else:
                kwargs[arg] = context.view.kwargs[arg]

        # parent url
        router_name = parent.viewset.get_router_name(self.key_target)
        vs_url = reverse(router_name, kwargs=kwargs)

        # get the url for the target key
        dict_kwargs.update(
            vs_url=vs_url
        )

        # check permission
        if cls.vs_has_access(context.view.request.user, context.object):
            dict_kwargs.update(
                vs_access=True,
            )

        data = cls.vs_get_dict(context=context, **dict_kwargs)
        return data


class FilterContextButton:
    """
    A context button that
    """

    key: str = "filter"

    def get_context(self, context: ViewContext) -> dict:
        from ..views import ListViewTableFilterMixin

        dict_kwargs = dict(
            vs_access=False
        )

        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
           return dict_kwargs

        # todo, check permission

        list_url = context.view.vs_get_url(key=context.view.vs_key)

        data = dict()

        # render action label
        vs_action_label = "Filter"  # todo, add render
        if vs_action_label:
            data["vs_action_label"] = vs_action_label

        data["vs_icon_action"] = "fa-solid fa-filter"
        # "fa-solid fa-filter-circle-xmark"
        # data["vs_url"] = "#filter-collapse"
        data["vs_url"] = list_url

        data["vs_template"] = f"{crud_views_settings.theme_path}/tags/context_action_filter.html"

        # data["vs_url"] = "javascript:alert(1);return false;"

        return data
