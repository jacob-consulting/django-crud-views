from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Type, Any, Iterable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from crud_views.lib.viewset import ViewSet
    from django.contrib.auth.models import AbstractUser as User

from crud_views.lib import check
from crud_views.lib.check import (
    Check,
    CheckAttributeReg,
    CheckAttribute,
    CheckTemplateOrCode,
    CheckTemplate,
    CheckExpression,
)
from crud_views.lib.exceptions import cv_raise, ParentViewSetError, CrudViewError, ViewSetKeyFoundError
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Model
from django.shortcuts import get_object_or_404
from django.template import Context as TemplateContext, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from typing_extensions import Self

from .buttons import ContextButton
from .context import ViewContext
from .meta import CrudViewMetaClass
from ..settings import crud_views_settings


def cv_is_modal_request(request) -> bool:
    """True when the client asked for the modal partial (X-CV-Modal header)."""
    return request.headers.get("X-CV-Modal") == "true"


class CrudView(metaclass=CrudViewMetaClass):
    """
    A view that is part of a ViewSet
    """

    cv_viewset: "ViewSet" = None
    cv_key: str = None  # the key to register the view (i.e. detail, list, create, update, delete)
    cv_path: str = None  # i.e. detail, update or "" for list views
    cv_object: bool = True  # view has object context (only list views do not have object context)
    cv_backend_only: bool = (
        False  # views is only available in the backend, so i.e. title and paragraph templates are not required
    )
    cv_list_actions: List[str] | None = None  # actions for the list view
    cv_list_action_method: str = "get"  # method to call for list actions
    cv_context_actions: List[str] | None = None  # context actions for the view (top right)
    cv_context_buttons: List[ContextButton] | None = None  # view-level context button definitions (issue #27)
    cv_home_key: str | None = "list"  # home url, defaults to list
    cv_success_key: str | None = "list"  # success url, defaults to list
    cv_cancel_key: str | None = "list"  # cancel url, defaults to list
    cv_parent_key: str | None = "list"  # parent key, defaults to list todo: does this make sense at all?

    cv_extends_template: str | None = None  # template to extend

    # modal rendering (Bootstrap 5 theme; see superpowers/specs/2026-07-14-bootstrap-modals-design.md)
    cv_modal: bool = False  # opt-in: action buttons open this view in a modal
    cv_modal_size: str = ""  # "" | "modal-sm" | "modal-lg" | "modal-xl"
    cv_modal_supported: bool = False  # phase gate: which view types may set cv_modal
    cv_content_template: str | None = None  # the view's body partial, shared by full page and modal

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
    cv_message_template: str | None = None  # success message template snippet
    cv_message_template_code: str | None = None  # success message template code
    cv_message_template_error: str | None = None  # error message template snippet
    cv_message_template_error_code: str | None = None  # error message template code

    # icons
    cv_icon_action: str | None = None  # font awesome icon
    cv_icon_header: str | None = None  # font awesome icon

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield CheckAttributeReg(context=cls, id="E200", attribute="cv_key", **check.REGS["name"])
        yield CheckAttributeReg(context=cls, id="E201", attribute="cv_path", **check.REGS["path"])
        yield CheckTemplate(context=cls, id="E111", attribute="cv_extends_template")

        # templates are required for frontend views
        is_frontend = not cls.cv_backend_only
        if is_frontend:
            for attribute in [
                "cv_header_template",
                "cv_paragraph_template",
                "cv_action_label_template",
                "cv_action_short_label_template",
            ]:
                yield CheckTemplateOrCode(context=cls, attribute=attribute)

        yield CheckExpression(
            context=cls,
            id="E250",
            expression=cls.cv_modal_size in ("", "modal-sm", "modal-lg", "modal-xl"),
            msg=f"cv_modal_size must be one of '', 'modal-sm', 'modal-lg', 'modal-xl', got {cls.cv_modal_size!r}",
        )
        yield CheckExpression(
            context=cls,
            id="E251",
            expression=not cls.cv_modal or cls.cv_modal_supported,
            msg="cv_modal is not supported for this view type (phase 1: delete, detail and custom form views)",
        )

    def get_success_url(self) -> str:
        url = self.cv_get_url(key=self.cv_success_key, obj=getattr(self, "object", None))
        return url

    def get_queryset(self):
        return self.cv_viewset.get_queryset(view=self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cv_extends"] = self.cv_get_extends_template()
        return context

    def get_template_names(self):
        if self.cv_modal and cv_is_modal_request(self.request):
            return ["crud_views/modal/content.html"]
        return super().get_template_names()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.cv_modal:
            patch_vary_headers(response, ["X-CV-Modal"])
        return response

    def cv_get_extends_template(self) -> str:
        if self.cv_extends_template:
            return self.cv_extends_template
        if self.cv_viewset.extends:
            return self.cv_viewset.extends
        return crud_views_settings.extends

    @classmethod
    def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
        return True

    @classmethod
    def cv_action_enabled(cls, user: User, obj: Model | None = None) -> bool:
        """Secondary action gate, evaluated only AFTER cv_has_access has passed.

        cv_has_access answers "may you do this in principle?" (permission).
        cv_action_enabled answers "is this action currently applicable to THIS
        object?" (state) — e.g. an open/locked parent disables child create/delete.
        Both must be true for the action button to render and the request to be
        allowed. Default: always enabled.
        """
        return True

    def cv_get_action_object(self) -> Model | None:
        """The object an action concerns: the instance for object-views, the
        parent for child create-views, else None. Used by request enforcement."""
        if self.cv_object:
            return self.get_object()
        if self.cv_viewset.has_parent:
            return self.cv_get_parent_object()
        return None

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

    def cv_get_message(self, *, error: bool = False) -> str | None:
        """
        Render the success (default) or error message snippet.
        Returns None when the relevant template pair is not configured.
        """
        if error:
            template = self.cv_message_template_error
            template_code = self.cv_message_template_error_code
        else:
            template = self.cv_message_template
            template_code = self.cv_message_template_code
        if not template and not template_code:
            return None
        return self.render_snippet(self.cv_get_meta(), template, template_code)

    def cv_get_header_icon(self) -> str:
        view_icon = self.cv_icon_header
        icon = view_icon or self.cv_viewset.icon_header
        return icon

    @property
    def cv_header(self) -> str:
        return self.render_snippet(
            self.cv_get_meta(),
            self.cv_header_template,
            self.cv_header_template_code,
        )

    @property
    def cv_paragraph(self) -> str:
        return self.render_snippet(
            self.cv_get_meta(),
            self.cv_paragraph_template,
            self.cv_paragraph_template_code,
        )

    @classmethod
    def cv_get_action_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(
            cls.cv_viewset.get_meta(context),
            cls.cv_action_label_template,
            cls.cv_action_label_template_code,
        )

    @classmethod
    def cv_get_action_short_label(cls, context: ViewContext) -> str:
        return cls.render_snippet(
            cls.cv_viewset.get_meta(context),
            cls.cv_action_short_label_template,
            cls.cv_action_short_label_template_code,
        )

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
            cv_modal=cls.cv_modal,
            cv_modal_size=cls.cv_modal_size,
        )
        data["cv_is_active"] = cls.cv_viewset.get_router_name(cls.cv_key) == context.router_name
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

    def cv_get_router_and_args(
        self, key: str | None = None, obj=None, extra_kwargs: dict | None = None
    ) -> Tuple[str, tuple, dict]:
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
        # view-level buttons take precedence over ViewSet-level buttons (issue #27)
        for cb in self.cv_context_buttons or []:
            if cb.key == key:
                return cb
        for cb in self.cv_viewset.context_buttons:
            if cb.key == key:
                return cb
        return None

    def cv_get_context_buttons(self, keys: list[str] | None = None, obj=None) -> list[dict]:
        """
        Resolved, access-filtered context-button data for a custom template loop.
        keys defaults to this view's cv_context_actions; obj defaults to the view's object.
        """
        keys = keys if keys is not None else (self.cv_context_actions or [])
        if obj is None:
            obj = getattr(self, "object", None)
        result: list[dict] = []
        for key in keys:
            ctx = self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request)
            if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
                continue
            result.append(ctx)
        return result

    def cv_get_oid(self, key: str, obj: Model | None = None) -> str | None:
        """
        get unique object id
        """
        if not obj:
            return None
        pk = str(obj.pk).replace("-", "").replace(" ", "")
        return f"{self.cv_viewset.name}_{key}_{pk}"

    def cv_get_context(
        self, key: str | None = None, obj: Model | None = None, user: User | None = None, request=None
    ) -> Dict[str, Any]:
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

        # get target view class; an unregistered key is not a misconfiguration here -> skip
        try:
            cls = self.cv_get_cls_assert_object(key, obj)
        except ViewSetKeyFoundError:
            return {}

        # the key is a view
        dict_kwargs = dict(
            cv_access=False,
            cv_oid=self.cv_get_oid(key=key, obj=obj),
            cv_url=self.cv_get_url(key=key, obj=obj),
            cv_template=crud_views_settings.context_button_template,
        )

        # set up the view context
        context = self.cv_get_view_context(object=obj)

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(user, obj)

        # check access
        if cls.cv_has_access(user, obj):
            dict_kwargs.update(
                cv_access=True,
            )

        # prepare dict
        data = cls.cv_get_dict(context=context, **dict_kwargs)

        return data

    def get_cancel_button_context(self, obj: Model | None = None, user: User | None = None, request=None) -> dict:
        """
        Get the context for the cancel button
        """
        url = self.cv_get_url(key=self.cv_cancel_key, obj=obj)
        return dict(cv_url=url, cv_action_label=_("Cancel"))

    def cv_get_child_url(self, name: str, key: str, obj: Model | None = None) -> str:
        """
        Get the URL to the child from the current CrudView's context
        """
        viewset = self.cv_viewset.get_viewset(name)
        if viewset.parent.name != self.cv_viewset.name:
            raise ParentViewSetError(f"ViewSet {viewset} is no child of {self.cv_viewset}")
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
        yield CheckAttribute(context=cls, id="E202", attribute="cv_permission")

    @cached_property
    def permission_required(self) -> str:
        cv_raise(self.cv_permission is not None, f"cv_permission not set at {self}")
        perms = self.cv_viewset.permissions  # noqa
        perm = perms.get(self.cv_permission)
        assert perm, f"permission {self.cv_permission} not found at {self}"
        return perm

    def has_permission(self):
        if not super().has_permission():
            return False
        # Secondary state gate — a disabled action is denied even with permission.
        # Note: cv_get_action_object() re-fetches the object (object views call
        # get_object() again in the body — a deliberate extra read), and a missing
        # pk raises Http404 here, so a bad-pk request 404s during the permission
        # phase rather than reaching the view. Returning False yields 403 for an
        # authenticated user (login redirect for anonymous — the pre-existing contract).
        obj = self.cv_get_action_object()
        return self.cv_action_enabled(self.request.user, obj)

    @classmethod
    def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        perms = (perm,) if perm else tuple()
        has_access = user.has_perms(perms)
        return has_access
