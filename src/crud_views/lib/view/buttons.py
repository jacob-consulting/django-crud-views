from django.urls import reverse
from pydantic import BaseModel

from .context import ViewContext
from ..settings import crud_views_settings


class ContextButton(BaseModel):
    """
    A context button is a button that is rendered in the context of a CrudView
    """

    key: str
    key_target: str | None = None
    label_template: str | None = None
    label_template_code: str | None = None

    @staticmethod
    def _resolve_container_key(viewset, key_target: str) -> str:
        if key_target == "list" and not viewset.is_view_registered("list"):
            if viewset.is_view_registered("card"):
                return "card"
        return key_target

    def render_label(self, data: dict, context: ViewContext) -> str:
        if self.label_template:
            return context.view.render_snippet(data, self.label_template)
        elif self.label_template_code:
            return context.view.render_snippet(data, template_code=self.label_template_code)

    def get_context(self, context: ViewContext) -> dict:
        key_target = self._resolve_container_key(context.view.cv_viewset, self.key_target)

        dict_kwargs = dict(cv_access=False, cv_url=context.view.cv_get_url(key=key_target, obj=context.object))

        # get target view class
        cls = context.view.cv_get_cls_assert_object(key_target, context.object)

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
        key_target = self._resolve_container_key(parent.viewset, self.key_target)
        cls = parent.viewset.get_view_class(key_target)

        dict_kwargs = dict(cv_access=False, cv_icon_action=cls.cv_viewset.icon_header)

        # parent url kwargs
        kwargs = dict()
        for idx, arg in enumerate(context.view.cv_viewset.get_parent_url_args()):
            if idx == 0:
                if cls.cv_object:
                    kwargs[parent.viewset.pk_name] = context.view.kwargs[arg]
            else:
                kwargs[arg] = context.view.kwargs[arg]

        # parent url
        router_name = parent.viewset.get_router_name(key_target)
        cv_url = reverse(router_name, kwargs=kwargs)

        # get the url for the target key
        dict_kwargs.update(cv_url=cv_url)

        # check permission
        if cls.cv_has_access(context.view.request.user, context.object):
            dict_kwargs.update(
                cv_access=True,
            )

        data = cls.cv_get_dict(context=context, **dict_kwargs)
        return data


class ChildContextButton(ContextButton):
    """
    A context button that links to a child viewset (e.g. from parent detail to child list).
    """

    child_name: str
    child_key: str = "list"

    def get_context(self, context: ViewContext) -> dict:
        if context.object is None:
            return dict()

        child_vs = context.view.cv_viewset.get_viewset(self.child_name)
        cls = child_vs.get_view_class(self.child_key)

        url = context.view.cv_get_child_url(self.child_name, self.child_key, context.object)

        dict_kwargs = dict(
            cv_access=False,
            cv_url=url,
            cv_icon_action=child_vs.icon_header,
        )

        if cls.cv_has_access(context.view.request.user, context.object):
            dict_kwargs.update(cv_access=True)

        data = cls.cv_get_dict(context=context, **dict_kwargs)

        cv_action_label = self.render_label(data, context)
        if cv_action_label:
            data["cv_action_label"] = cv_action_label

        return data


class FilterContextButton(ContextButton):
    """
    A context button that
    """

    key: str = "filter"

    def get_context(self, context: ViewContext) -> dict:
        from ..views import ListViewTableFilterMixin

        dict_kwargs = dict(cv_access=False)

        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
            return dict_kwargs

        list_url = context.view.cv_get_url(key=context.view.cv_key)

        data = dict()

        # render action label
        cv_action_label = "Filter"
        if cv_action_label:
            data["cv_action_label"] = cv_action_label

        data["cv_icon_action"] = crud_views_settings.filter_icon
        data["cv_url"] = list_url
        data["cv_template"] = f"{crud_views_settings.theme_path}/tags/context_action_filter.html"

        return data
