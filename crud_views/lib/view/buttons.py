from django.contrib.auth import get_user_model
from django.urls import reverse
from pydantic import BaseModel

from .context import ViewContext
from ..settings import crud_views_settings
from ..exceptions import CrudViewError

User = get_user_model()


class ContextButton(BaseModel):
    """
    A context button is a button that is rendered in the context of a CrudView
    """
    key: str
    key_target: str | None = None
    label_template: str | None = None
    label_template_code: str | None = None

    def render_label(self, data: dict, context: ViewContext) -> str:
        if self.label_template:
            return context.view.render_snippet(data, self.label_template)
        elif self.label_template_code:
            return context.render_snippet(data, template_code=self.label_template_code)

    def get_context(self, context: ViewContext) -> dict:

        dict_kwargs = dict(
            cv_access=False,
            cv_url=context.view.cv_get_url(key=self.key_target, obj=context.object)
        )

        # get target view class
        cls = context.view.cv_get_cls_assert_object(self.key_target, context.object)

        # check access
        if cls.cv_has_access(context.view.request.user, context.object):
            # get the url for the target key
            dict_kwargs.update(
                cv_access=True,
            )

        # final data
        data = cls.cv_get_dict(context=context, **dict_kwargs)

        # render action label
        cv_action_label = self.render_label(data, context)
        if cv_action_label:
            data["cv_action_label"] = cv_action_label

        return data


class ParentContextButton(ContextButton):
    """
    A context button that
    """

    def get_context(self, context: ViewContext) -> dict:

        # does the view has no parent?
        if not context.view.cv_viewset.parent:
            return dict()

        # get the parent view class, defined by target
        parent = context.view.cv_viewset.parent
        cls = parent.viewset.get_view_class(self.key_target)

        dict_kwargs = dict(
            cv_access=False,
            cv_icon_action=cls.cv_viewset.icon_header
        )

        # parent url kwargs
        kwargs = dict()
        for idx, arg in enumerate(context.view.cv_viewset.get_parent_url_args()):
            if idx == 0:
                if cls.cv_object:
                    kwargs[parent.viewset.pk_name] = context.view.kwargs[arg]
            else:
                kwargs[arg] = context.view.kwargs[arg]

        # parent url
        router_name = parent.viewset.get_router_name(self.key_target)
        cv_url = reverse(router_name, kwargs=kwargs)

        # get the url for the target key
        dict_kwargs.update(
            cv_url=cv_url
        )

        # check permission
        if cls.cv_has_access(context.view.request.user, context.object):
            dict_kwargs.update(
                cv_access=True,
            )

        data = cls.cv_get_dict(context=context, **dict_kwargs)
        return data


class FilterContextButton(ContextButton):
    """
    A context button that
    """

    key: str = "filter"

    def get_context(self, context: ViewContext) -> dict:
        from ..views import ListViewTableFilterMixin

        dict_kwargs = dict(
            cv_access=False
        )

        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
           return dict_kwargs

        # todo, check permission

        list_url = context.view.cv_get_url(key=context.view.cv_key)

        data = dict()

        # render action label
        cv_action_label = "Filter"  # todo, add render
        if cv_action_label:
            data["cv_action_label"] = cv_action_label

        data["cv_icon_action"] = "fa-solid fa-filter"
        # "fa-solid fa-filter-circle-xmark"
        # data["cv_url"] = "#filter-collapse"
        data["cv_url"] = list_url

        data["cv_template"] = f"{crud_views_settings.theme_path}/tags/context_action_filter.html"

        # data["cv_url"] = "javascript:alert(1);return false;"

        return data
