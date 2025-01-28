from functools import cached_property
from typing import Dict, List, Type, Any, Iterable

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Model
from django.template import Context as TemplateContext, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from typing_extensions import Self

from crud_views.lib import check
from crud_views.lib.check import Check, CheckAttributeReg, CheckExpression, CheckEitherAttribute, ContextActionCheck, \
    CheckAttribute, CheckAttributeTemplate
from crud_views.lib.exceptions import vs_raise, ParentViewSetError, ViewSetViewError
from .buttons import ContextButton
from .context import ViewContext
from .meta import ViewSetViewMetaClass
from ..settings import crud_views_settings

User = get_user_model()


class ViewSetView(metaclass=ViewSetViewMetaClass):
    """
    A view that is part of a ViewSet
    """
    vs: 'ViewSet' = None
    vs_object: bool = True  # view has object context (only list views do not have object context)
    vs_key: str = None  # the key to register the view (i.e. detail, list, create, update, delete)
    vs_path: str = None  # i.e. detail, update or "" for list views
    vs_backend_only: bool = False  # views is only available in the backend, so i.e. title and paragraph templates are not required
    vs_list_actions: List[str] | None = None  # actions for the list view
    vs_list_action_method: str = "get"  # method to call for list actions
    vs_context_actions: List[str] | None = None  # context actions for the view (top right)
    vs_home_key: str | None = "list"  # home url, defaults to list
    vs_success_key: str | None = "list"  # success url, defaults to list
    vs_cancel_key: str | None = "list"  # cancel url, defaults to list
    vs_parent_key: str | None = "list"  # parent key, defaults to list todo: does this make sense at all?

    # texts and labels
    vs_header_template: str | None = None  # template snippet to render header label
    vs_header_template_code: str | None = None  # template code to render header label
    vs_paragraph_template: str | None = None  # template snippet to render paragraph
    vs_paragraph_template_code: str | None = None  # template code to render paragraph
    vs_action_label_template: str | None = None  # template snippet to render action label
    vs_action_label_template_code: str | None = None  # template code to render action label
    vs_action_short_label_template: str | None = None  # template snippet to render short action label without icons
    vs_action_short_label_template_code: str | None = None  # template code to render short  action label  without icons

    # icons
    vs_icon_action: str | None = None  # font awesome icon
    vs_icon_header: str | None = None  # font awesome icon

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield CheckAttributeReg(context=cls, id="E200", attribute="vs_key", **check.REGS["name"])
        yield CheckAttributeReg(context=cls, id="E201", attribute="vs_path", **check.REGS["path"])

        # todo: reactivate
        # yield ContextActionCheck(context=cls, id="E203", msg="action not defined")

        # templates are required for frontend views
        is_frontend = not cls.vs_backend_only
        if is_frontend:
            for a1, a2 in [
                ("vs_header_template", "vs_header_template_code"),
                ("vs_paragraph_template", "vs_paragraph_template_code"),
                ("vs_action_label_template", "vs_action_label_template_code"),
                ("vs_action_short_label_template", "vs_action_short_label_template_code"),
            ]:
                yield CheckEitherAttribute(context=cls, id="E203", attribute1=a1, attribute2=a2)
                yield CheckAttributeTemplate(context=cls, attribute=a1)

    def get_success_url(self) -> str:
        url = self.vs_get_url(key=self.vs_success_key)
        return url

    def get_queryset(self):
        return self.vs.get_queryset(view=self)

    @classmethod
    def vs_has_access(cls, user: User, obj: Model | None = None) -> bool:
        return True

    @classmethod
    def render_snippet(cls, data: dict, template: str = None, template_code: str = None) -> str:
        """
        Either render the template_code or the template
        """
        if template_code:
            template = Template(template_code)
            context = TemplateContext(data)
            result = template.render(context)
        elif template:
            result = render_to_string(template, data)
        else:
            raise ViewSetViewError(f"no template or template_code provided for {cls}")

        # strip leading and trailing whitespaces and mark it as safe
        return mark_safe(result.strip())

    def vs_get_header_icon(self) -> str:
        view_icon = self.vs_icon_header
        icon = view_icon or self.vs.icon_header
        return icon

    @property
    def vs_header(self) -> str:
        return self.render_snippet(self.vs_get_meta(),
                                   self.vs_header_template,
                                   self.vs_header_template_code, )

    @property
    def vs_paragraph(self) -> str:
        return self.render_snippet(self.vs_get_meta(),
                                   self.vs_paragraph_template,
                                   self.vs_paragraph_template_code, )

    @classmethod
    def vs_get_action_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(cls.vs.get_meta(context),
                                  cls.vs_action_label_template,
                                  cls.vs_action_label_template_code, )

    @classmethod
    def vs_get_action_short_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(cls.vs.get_meta(context),
                                  cls.vs_action_short_label_template,
                                  cls.vs_action_short_label_template_code, )

    @classmethod
    def vs_get_dict(cls, context: ViewContext, **extra) -> Dict[str, Any]:
        """
        Note: This is a classmethod, so the view instance and it's object context is not available here.
              The data this method returns is used to link sibling views.
        """
        data = dict(
            vs_key=cls.vs_key,
            vs_path=cls.vs_path,
            vs_action_label=cls.vs_get_action_label(context=context),
            vs_action_short_label=cls.vs_get_action_short_label(context=context),
            vs_list_actions=cls.vs_list_actions,
            vs_list_action_method=cls.vs_list_action_method,
            vs_context_actions=cls.vs_context_actions,
            vs_home_key=cls.vs_home_key,
            vs_success_key=cls.vs_success_key,
            vs_cancel_key=cls.vs_cancel_key,
            vs_icon_action=cls.vs_icon_action,
            vs_icon_header=cls.vs_icon_header,
        )
        data.update(extra)
        return data

    @classmethod
    def vs_path_contribute(cls) -> str:
        """
        Contribute path to the path of the view
        """
        return ""

    def vs_get_cls(self, key: str | None = None) -> Type[Self]:
        """
        Get the class of the view or for a sibling of the view from ViewSet
        """
        key = key or self.vs_key
        cls = self.__class__ if key == self.vs_key else self.vs.get_view_class(key)
        return cls

    def vs_get_cls_assert_object(self, key: str | None = None, obj: Model | None = None) -> Type[Self]:
        """
        See vs_get_cls, but assert object context
        """
        cls = self.vs_get_cls(key)
        vs_raise(cls.vs_object is False or cls.vs_object is True and obj, f"view {cls} requires object")
        return cls

    @classmethod
    def vs_get_url_extra_kwargs(cls) -> dict:
        return dict()

    def vs_get_url(self, key: str | None = None, obj=None, extra_kwargs: dict | None = None) -> str:
        """
        Get the url for a sibling defined by key
        """
        cls = self.vs_get_cls_assert_object(key, obj)

        if extra_kwargs:
            assert isinstance(extra_kwargs, dict)
        kwargs = extra_kwargs if extra_kwargs else dict()

        # if view requires object, add pk using the pk_name defined at ViewSet
        if cls.vs_object:
            kwargs[self.vs.pk_name] = obj.pk

        # get kwargs to pass
        #   1. parent kwargs
        #   2. extra kwargs defined at ViewSet
        #   3. additional kwargs provided by ViewSetView
        parent_url_args = self.vs.get_parent_url_args()
        for name in parent_url_args:
            value = self.kwargs.get(name)
            if not value:
                raise ValueError(f"kwarg {name} not found at {self}")
            kwargs[name] = value
        kwargs.update(cls.vs_get_url_extra_kwargs())

        router_name = self.vs.get_router_name(key)
        url_path = reverse(router_name, kwargs=kwargs)

        return url_path

    def vs_get_view_context(self, **kwargs) -> ViewContext:
        """
        Get the context for the view
        """
        if self.vs_object and "object" not in kwargs:
            kwargs["object"] = self.object

        if "view" not in kwargs:
            kwargs["view"] = self

        return ViewContext(**kwargs)

    def vs_get_context_button(self, key: str) -> ContextButton | None:
        # todo: first look in ViewSetView context_buttons
        pass

        # then look as ViewSet context_buttons
        for cb in self.vs.context_buttons:
            if cb.key == key:
                return cb
        return None

    def vs_get_oid(self, key: str,
                   obj: Model | None = None) -> str | None:
        """
        get unique object id
        """
        if not obj:
            return None
        pk = str(obj.pk).replace("-", "").replace(" ", "")
        return f"{self.vs.name}_{key}_{pk}"

    def vs_get_context(self,
                       key: str | None = None,
                       obj: Model | None = None,
                       user: User | None = None,
                       request=None) -> Dict[str, Any]:
        """
        Get template context for this view for a key and an optional object
        """

        # first get the view context
        context = self.vs_get_view_context(object=obj)

        # is the key a context button?
        context_button = self.vs_get_context_button(key)
        if context_button:
            ctx = context_button.get_context(context)
            return ctx

        # the key is a view
        dict_kwargs = dict(
            vs_access=False,
            vs_oid=self.vs_get_oid(key=key, obj=obj),
            vs_url=self.vs_get_url(key=key, obj=obj)
        )

        # get target view class
        cls = self.vs_get_cls_assert_object(key, obj)

        # set up the view context
        context = self.vs_get_view_context(object=obj)

        # check access
        if cls.vs_has_access(user, obj):
            dict_kwargs.update(
                vs_access=True,
            )

        # prepare dict
        data = cls.vs_get_dict(context=context, **dict_kwargs)

        return data

    def get_cancel_button_context(self,
                                  obj: Model | None = None,
                                  user: User | None = None,
                                  request=None) -> dict:
        """
        Get the context for the cancel button
        """
        url = self.vs_get_url(key=self.vs_cancel_key, obj=obj)
        return dict(
            vs_url=url,
            vs_action_label=_("Cancel")
        )

    def vs_get_child_url(self, name: str, key: str, obj: Model | None = None) -> str:
        """
        Get the URL to the child from the current ViewSetView's context
        """
        viewset = self.vs.get_viewset(name)
        if viewset.parent.name != self.vs.name:
            raise ParentViewSetError(f"ViewSet {viewset} is no child of {self.vs}")
        # todo: check if this is a child of self.vs
        name = viewset.get_router_name(key)
        args = viewset.get_parent_url_args()
        attrs = viewset.get_parent_attributes()
        kw = dict()
        for idx, (arg, attr) in enumerate(zip(args, attrs)):
            if idx == 0 and obj:
                kw[arg] = obj.id  # it's me, because I'm linking to the child
            else:
                kw[arg] = self.kwargs[arg]  # get value from the view's kwargs
        url = reverse(name, kwargs=kw)
        return url

    def vs_get_meta(self) -> dict:
        """
        Metadata from ViewSet plus ViewContext
        """
        context = self.vs_get_view_context()
        data = self.vs.get_meta(context=context)

        # add view specific data
        if hasattr(self, "object"):
            data["object"] = self.object

        return data


# ViewContext uses a string type hint to ViewSetView, so we need to rebuild the model here
ViewContext.model_rebuild()


class ViewSetViewPermissionRequiredMixin(PermissionRequiredMixin):
    vs_permission: str = None  # permission required for the view

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()  # noqa
        # todo
        yield CheckAttribute(context=cls, id="E202", attribute="vs_permission")

    @cached_property
    def permission_required(self) -> str:
        vs_raise(self.vs_permission is not None, f"vs_permission not set at {self}")
        perms = self.vs.permissions  # noqa
        perm = perms.get(self.vs_permission)
        assert perm, f"permission {self.vs_permission} not found at {self}"
        return perm

    @classmethod
    def vs_has_access(cls, user: User, obj: Model | None = None) -> bool:
        perm = cls.vs.permissions.get(cls.vs_permission)
        perms = (perm,) if perm else tuple()
        has_access = user.has_perms(perms)
        return has_access
