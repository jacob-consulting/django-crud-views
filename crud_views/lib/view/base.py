from functools import cached_property
from typing import Dict, List, Type, Any, Iterable, Tuple

from crud_views.lib import check
from crud_views.lib.check import Check, CheckAttributeReg, CheckAttribute, CheckTemplateOrCode
from crud_views.lib.exceptions import cv_raise, ParentViewSetError, CrudViewError
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Model
from django.shortcuts import get_object_or_404
from django.template import Context as TemplateContext, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from typing_extensions import Self

from .buttons import ContextButton
from .context import ViewContext
from .meta import CrudViewMetaClass
from ..settings import crud_views_settings

User = get_user_model()


class CrudView(metaclass=CrudViewMetaClass):
    """
    A view that is part of a ViewSet
    """
    cv_viewset: 'ViewSet' = None
    cv_key: str = None  # the key to register the view (i.e. detail, list, create, update, delete)
    cv_path: str = None  # i.e. detail, update or "" for list views
    cv_object: bool = True  # view has object context (only list views do not have object context)
    cv_backend_only: bool = False  # views is only available in the backend, so i.e. title and paragraph templates are not required
    cv_list_actions: List[str] | None = None  # actions for the list view
    cv_list_action_method: str = "get"  # method to call for list actions
    cv_context_actions: List[str] | None = None  # context actions for the view (top right)
    cv_home_key: str | None = "list"  # home url, defaults to list
    cv_success_key: str | None = "list"  # success url, defaults to list
    cv_cancel_key: str | None = "list"  # cancel url, defaults to list
    cv_parent_key: str | None = "list"  # parent key, defaults to list todo: does this make sense at all?

    cv_extends_template: str | None = None  # template to extend

    # texts and labels
    cv_header_template: str | None = None  # template snippet to render header label
    cv_header_template_code: str | None = None  # template code to render header label
    cv_paragraph_template: str | None = None  # template snippet to render paragraph
    cv_paragraph_template_code: str | None = None  # template code to render paragraph
    cv_action_label_template: str | None = None  # template snippet to render action label
    cv_action_label_template_code: str | None = None  # template code to render action label
    cv_action_short_label_template: str | None = None  # template snippet to render short action label without icons
    cv_action_short_label_template_code: str | None = None  # template code to render short  action label  without icons
    cv_filter_header_template: str | None = None  # template snippet to render filter header
    cv_filter_header_template_code: str | None = None  # template code to render filter header
    cv_message_template: str | None = None  # template snippet to render messages
    cv_message_template_code: str | None = None  # template code to render messages

    # icons
    cv_icon_action: str | None = None  # font awesome icon
    cv_icon_header: str | None = None  # font awesome icon

    # @classproperty
    # def model(self):
    #     return self.cv_viewset.model

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield CheckAttributeReg(context=cls, id="E200", attribute="cv_key", **check.REGS["name"])
        yield CheckAttributeReg(context=cls, id="E201", attribute="cv_path", **check.REGS["path"])

        # todo: cv_extends test template if defined

        # todo: reactivate
        # yield ContextActionCheck(context=cls, id="E203", msg="action not defined")

        # templates are required for frontend views
        is_frontend = not cls.cv_backend_only
        if is_frontend:
            for attribute in [
                "cv_header_template",
                "cv_paragraph_template",
                "cv_action_label_template",
                "cv_action_short_label_template"
            ]:
                yield CheckTemplateOrCode(context=cls, attribute=attribute)

    def get_success_url(self) -> str:
        url = self.cv_get_url(key=self.cv_success_key, obj=getattr(self, "object", None))
        return url

    def get_queryset(self):
        return self.cv_viewset.get_queryset(view=self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cv_extends"] = self.cv_get_extends_template()
        return context

    def cv_get_extends_template(self) -> str:
        cv_extends = self.cv_extends_template
        extends = cv_extends if cv_extends else crud_views_settings.extends
        return extends

    @classmethod
    def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
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
            raise CrudViewError(f"no template or template_code provided for {cls}")

        # strip leading and trailing whitespaces and mark it as safe
        return mark_safe(result.strip())

    def cv_get_header_icon(self) -> str:
        view_icon = self.cv_icon_header
        icon = view_icon or self.cv_viewset.icon_header
        return icon

    @property
    def cv_header(self) -> str:
        return self.render_snippet(self.cv_get_meta(),
                                   self.cv_header_template,
                                   self.cv_header_template_code, )

    @property
    def cv_paragraph(self) -> str:
        return self.render_snippet(self.cv_get_meta(),
                                   self.cv_paragraph_template,
                                   self.cv_paragraph_template_code, )

    @classmethod
    def cv_get_action_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(cls.cv_viewset.get_meta(context),
                                  cls.cv_action_label_template,
                                  cls.cv_action_label_template_code, )

    @classmethod
    def cv_get_action_short_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(cls.cv_viewset.get_meta(context),
                                  cls.cv_action_short_label_template,
                                  cls.cv_action_short_label_template_code, )

    @classmethod
    def cv_get_dict(cls, context: ViewContext, **extra) -> Dict[str, Any]:
        """
        Note: This is a classmethod, so the view instance and it's object context is not available here.
              The data this method returns is used to link sibling views.
        """
        data = dict(
            cv_key=cls.cv_key,
            cv_path=cls.cv_path,
            cv_action_label=cls.cv_get_action_label(context=context),
            cv_action_short_label=cls.cv_get_action_short_label(context=context),
            cv_list_actions=cls.cv_list_actions,
            cv_list_action_method=cls.cv_list_action_method,
            cv_context_actions=cls.cv_context_actions,
            cv_home_key=cls.cv_home_key,
            cv_success_key=cls.cv_success_key,
            cv_cancel_key=cls.cv_cancel_key,
            cv_icon_action=cls.cv_icon_action,
            cv_icon_header=cls.cv_icon_header,
        )
        data.update(extra)
        return data

    @classmethod
    def cv_path_contribute(cls) -> str:
        """
        Contribute path to the path of the view
        """
        return ""

    def cv_get_cls(self, key: str | None = None) -> Type[Self]:
        """
        Get the class of the view or for a sibling of the view from ViewSet
        """
        key = key or self.cv_key
        cls = self.__class__ if key == self.cv_key else self.cv_viewset.get_view_class(key)
        return cls

    def cv_get_cls_assert_object(self, key: str | None = None, obj: Model | None = None) -> Type[Self]:
        """
        See cv_get_cls, but assert object context
        """
        cls = self.cv_get_cls(key)
        cv_raise(cls.cv_object is False or cls.cv_object is True and obj, f"view {cls} requires object")
        return cls

    @classmethod
    def cv_get_url_extra_kwargs(cls) -> dict:
        return dict()

    def cv_get_router_and_args(self, key: str | None = None, obj=None, extra_kwargs: dict | None = None) -> Tuple[
        str, tuple, dict]:
        """
        Get the router name, args, kwargs url for a sibling defined by a key
        """
        cls = self.cv_get_cls_assert_object(key, obj)

        if extra_kwargs:
            assert isinstance(extra_kwargs, dict)
        kwargs = extra_kwargs if extra_kwargs else dict()
        args = []

        # if the view requires an object, add pk using the pk_name defined at ViewSet
        if cls.cv_object:
            kwargs[self.cv_viewset.pk_name] = obj.pk
            args.append(obj.pk)

        # get kwargs to pass
        #   1. parent kwargs
        #   2. extra kwargs defined at ViewSet
        #   3. additional kwargs provided by CrudView
        parent_url_args = self.cv_viewset.get_parent_url_args()
        for name in parent_url_args:
            value = self.kwargs.get(name)
            if not value:
                raise ValueError(f"kwarg {name} not found at {self}")
            kwargs[name] = value
            args.append(value)
        kwargs.update(cls.cv_get_url_extra_kwargs())

        args.reverse()
        router_name = self.cv_viewset.get_router_name(key)
        return router_name, tuple(args), kwargs

    def cv_get_url(self, key: str | None = None, obj=None, extra_kwargs: dict | None = None) -> str:
        """
        Get the url for a sibling defined by key
        """
        router_name, args, kwargs = self.cv_get_router_and_args(key=key, obj=obj, extra_kwargs=extra_kwargs)
        url_path = reverse(router_name, kwargs=kwargs)
        return url_path

    def cv_get_view_context(self, **kwargs) -> ViewContext:
        """
        Get the context for the view
        """
        if self.cv_object and "object" not in kwargs:
            kwargs["object"] = self.object

        if "view" not in kwargs:
            kwargs["view"] = self

        return ViewContext(**kwargs)

    def cv_get_context_button(self, key: str) -> ContextButton | None:
        # todo: first look in CrudView context_buttons
        pass

        # then look as ViewSet context_buttons
        for cb in self.cv_viewset.context_buttons:
            if cb.key == key:
                return cb
        return None

    def cv_get_oid(self, key: str,
                   obj: Model | None = None) -> str | None:
        """
        get unique object id
        """
        if not obj:
            return None
        pk = str(obj.pk).replace("-", "").replace(" ", "")
        return f"{self.cv_viewset.name}_{key}_{pk}"

    def cv_get_context(self,
                       key: str | None = None,
                       obj: Model | None = None,
                       user: User | None = None,
                       request=None) -> Dict[str, Any]:
        """
        Get template context for this view for a key and an optional object
        """

        # first get the view context
        context = self.cv_get_view_context(object=obj)

        # is the key a context button?
        context_button = self.cv_get_context_button(key)
        if context_button:
            ctx = context_button.get_context(context)
            return ctx

        # the key is a view
        dict_kwargs = dict(
            cv_access=False,
            cv_oid=self.cv_get_oid(key=key, obj=obj),
            cv_url=self.cv_get_url(key=key, obj=obj),
            cv_is_active=self.cv_viewset.get_router_name(key) == context.router_name,
        )

        # get target view class
        cls = self.cv_get_cls_assert_object(key, obj)

        # set up the view context
        context = self.cv_get_view_context(object=obj)

        # check access
        if cls.cv_has_access(user, obj):
            dict_kwargs.update(
                cv_access=True,
            )

        # prepare dict
        data = cls.cv_get_dict(context=context, **dict_kwargs)

        return data

    def get_cancel_button_context(self,
                                  obj: Model | None = None,
                                  user: User | None = None,
                                  request=None) -> dict:
        """
        Get the context for the cancel button
        """
        url = self.cv_get_url(key=self.cv_cancel_key, obj=obj)
        return dict(
            cv_url=url,
            cv_action_label=_("Cancel")
        )

    def cv_get_child_url(self, name: str, key: str, obj: Model | None = None) -> str:
        """
        Get the URL to the child from the current CrudView's context
        """
        viewset = self.cv_viewset.get_viewset(name)
        if viewset.parent.name != self.cv_viewset.name:
            raise ParentViewSetError(f"ViewSet {viewset} is no child of {self.cv_viewset}")
        # todo: check if this is a child of self.cv
        name = viewset.get_router_name(key)
        args = viewset.get_parent_url_args()
        attrs = viewset.get_parent_attributes()
        kw = dict()
        for idx, (arg, attr) in enumerate(zip(args, attrs)):
            if idx == 0 and obj:
                kw[arg] = obj.pk  # it's me, because I'm linking to the child
            else:
                kw[arg] = self.kwargs[arg]  # get value from the view's kwargs
        url = reverse(name, kwargs=kw)
        return url

    def cv_get_meta(self) -> dict:
        """
        Metadata from ViewSet plus ViewContext
        """
        context = self.cv_get_view_context()
        data = self.cv_viewset.get_meta(context=context)

        # add view specific data
        if hasattr(self, "object"):
            data["object"] = self.object

        return data

    def cv_assert_parent(self):
        assert self.cv_viewset.has_parent, f"ViewSet {self.cv_name} has no parent"

    def cv_get_parent_object(self) -> Model:
        """
        Get parent object based on the view's kwargs
        """
        self.cv_assert_parent()

        assert self.cv_viewset.has_parent, "this ViewSet has no parent"

        # get the parent object
        parent_model = self.cv_viewset.get_parent_model()
        arg = self.cv_viewset.get_parent_url_args(first_only=True)
        pk = self.kwargs[arg]  # noqa
        return get_object_or_404(parent_model, pk=pk)

    def cv_get_parent_object_attribute(self) -> str:
        """
        Get the attribute/field that points to the parent object
        """
        self.cv_assert_parent()

        return self.cv_viewset.get_parent_attributes(first_only=True)


# ViewContext uses a string type hint to CrudView, so we need to rebuild the model here
ViewContext.model_rebuild()


class CrudViewPermissionRequiredMixin(PermissionRequiredMixin):
    cv_permission: str = None  # permission required for the view

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()  # noqa
        # todo
        yield CheckAttribute(context=cls, id="E202", attribute="cv_permission")

    @cached_property
    def permission_required(self) -> str:
        cv_raise(self.cv_permission is not None, f"cv_permission not set at {self}")
        perms = self.cv_viewset.permissions  # noqa
        perm = perms.get(self.cv_permission)
        assert perm, f"permission {self.cv_permission} not found at {self}"
        return perm

    @classmethod
    def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        perms = (perm,) if perm else tuple()
        has_access = user.has_perms(perms)
        return has_access
