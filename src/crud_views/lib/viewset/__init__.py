import threading
from collections import OrderedDict
from collections.abc import Iterable
from functools import cached_property
from typing import ClassVar, Literal, Self

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q, QuerySet
from django.urls import URLResolver, re_path
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from pydantic import BaseModel, Field, PrivateAttr, field_validator, model_validator

from crud_views.lib.ancestor_policy import AncestorPermissions as AncestorPermissions
from crud_views.lib.ancestor_policy import AncestorPolicy
from crud_views.lib.ancestors import _permission_key, _validate_ancestor_structure, _walk_ancestors
from crud_views.lib.exceptions import ViewSetKeyFoundError, ViewSetNotFoundError, cv_raise
from crud_views.lib.lazy import LazyStr
from crud_views.lib.resource import Resource
from crud_views.lib.viewset import path_regs

from .. import check
from ..button_classes import FORM_KINDS
from ..check import Check, CheckAttributeReg, CheckExpression, CheckTemplate
from ..settings import crud_views_settings
from ..view import (
    ContextButton,
    CrudView,
    ViewContext,
)
from ..view import (
    CrudViewPermissionRequiredMixin as CrudViewPermissionRequiredMixin,
)
from ..view.action_menu import cv_is_form_label_mode_map
from ..view.buttons import context_button_checks, context_buttons_default
from ..view.label_mode import LABEL_MODES, is_label_mode_map
from ..views.manage import ManageView
from .parentviewset import ParentViewSet
from .path_regs import PrimaryKeys


def empty_dict() -> dict:
    return {}


_REGISTRY = OrderedDict()
_REGISTRY_LOCK = threading.Lock()


class ViewSet(BaseModel):
    """
    Manages CRUD collections of views

    Default views are
    - list      : list collection of objects
    - detail    : detail view of an object
    - create    : create a new object
    - update    : update an existing object
    - delete    : delete an existing object

    Which ap to the following default permissions:
    - list      : view
    - detail    : view
    - create    : add
    - update    : change
    - delete    : delete
    """

    PK: ClassVar[type[PrimaryKeys]] = PrimaryKeys
    # ancestor permission provider when ``ancestor_policy.provider`` is None (core: model permissions)
    _ancestor_provider: ClassVar[str] = "model"

    model: type[Model] | type[Resource]
    name: str
    prefix: str | None = None
    app: str | None = None
    pk: str | None = None  # auto-detected from model if not set
    pk_name: str = "pk"
    context_buttons: list[ContextButton] = Field(default_factory=context_buttons_default)
    parent: ParentViewSet | None = None
    ordering: str | None = None
    icon_header: str | None = None
    # label override (#338): replaces model/Resource _meta names in get_meta(); None: model names
    verbose_name: LazyStr | None = None
    verbose_name_plural: LazyStr | None = None
    manage_view_class: str | None = None
    extends: str | None = None  # base template all views in this viewset extend
    inaccessible_actions: Literal["hide", "disable"] | None = None  # None: CRUD_VIEWS_INACCESSIBLE_ACTIONS
    # overflow menu (#174): keys that stay inline buttons; None: CRUD_VIEWS_*_ACTIONS_INLINE
    list_actions_inline: list[str] | tuple[str, ...] | None = None
    context_actions_inline: list[str] | tuple[str, ...] | None = None
    card_actions_inline: list[str] | tuple[str, ...] | None = None
    # label mode of context / list actions (#216): action key -> "label" | "icon" | "both";
    # None: CRUD_VIEWS_*_ACTIONS_LABEL_MODE
    context_actions_label_mode: dict[str, str] | None = None
    list_actions_label_mode: dict[str, str] | None = None
    # label mode of crispy form buttons (Phase 6): form kind -> mode; None: CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE
    form_actions_label_mode: dict[str, str] | None = None
    # Resource-based ViewSets only: explicit permission map, e.g.
    # {"view": "storage.view_s3object", "delete": "storage.delete_s3object"}.
    # None means: no permissions declared (only non-PermissionRequired views).
    resource_permissions: dict[str, str] | None = None
    # ancestor authorization (phase 06.18): provider/fallback apply when this ViewSet is an ancestor,
    # cascade/read/write/actions to requests targeting it; see crud_views.lib.ancestors
    ancestor_policy: AncestorPolicy = Field(default_factory=AncestorPolicy)

    _views: dict[str, type[CrudView]] = PrivateAttr(default_factory=empty_dict)
    _default_permissions: OrderedDict[str, str] | None = PrivateAttr(default=None)

    def __repr__(self):
        return f"ViewSet({self.name})"

    def __str__(self):
        return f"{self.name}"

    @property
    def is_resource(self) -> bool:
        return issubclass(self.model, Resource)

    @field_validator("context_actions_label_mode", "list_actions_label_mode")
    @classmethod
    def check_label_mode_map(cls, value):
        """The dict shape is Pydantic's; the values must be label modes (#216)."""
        if not is_label_mode_map(value):
            raise ValueError(f"must map action keys to one of {sorted(LABEL_MODES)}, got {value!r}")
        return value

    @field_validator("form_actions_label_mode")
    @classmethod
    def check_form_label_mode_map(cls, value):
        """Form kinds are finite (Phase 6): the keys must be FORM_KINDS, the values label modes."""
        if value is not None and not cv_is_form_label_mode_map(value):
            raise ValueError(f"must map form kinds {sorted(FORM_KINDS)} to one of {sorted(LABEL_MODES)}, got {value!r}")
        return value

    @field_validator("verbose_name", "verbose_name_plural")
    @classmethod
    def check_verbose_name(cls, value):
        """A plain str must not be blank (#338). Lazy values are not evaluated: str() of a gettext_lazy raises
        AppRegistryNotReady while apps load, and ViewSets are built at import time."""
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"must not be blank, got {value!r}")
        return value

    def _validate_ancestor_policy(self) -> None:
        """Owning-ViewSet constraints of ``ancestor_policy``, decidable at construction (no database, no other
        ViewSet). Called by ``register()`` before any registry or manage-view side effect."""
        policy = self.ancestor_policy
        if not isinstance(policy, AncestorPolicy):  # e.g. a subclass default given as a mapping
            policy = self.ancestor_policy = AncestorPolicy.model_validate(policy)
        class_provider = type(self)._ancestor_provider
        if policy.provider == "guardian" and class_provider != "guardian":
            raise ValueError(
                f"ancestor_policy.provider='guardian' is not supported by {type(self).__name__} {self.name!r}: "
                f"use GuardianViewSet for object-permission ancestors"
            )
        provider = policy.provider if policy.provider is not None else class_provider
        if policy.accept_global_perms and provider != "guardian":
            raise ValueError(
                f"ancestor_policy.accept_global_perms=True has no effect on ViewSet {self.name!r}: its ancestor "
                f"provider is {provider!r}, the flag applies only to a Guardian provider"
            )
        if self.parent is None:
            ineffective = [field for field in ("cascade", "read", "write") if getattr(policy, field) is not None] + (
                ["actions"] if policy.actions else []
            )
            if ineffective:
                raise ValueError(
                    f"ancestor_policy fields {', '.join(ineffective)} of top-level ViewSet {self.name!r} have no "
                    f"effect: they describe requests to a nested ViewSet (leave them None/empty)"
                )

    @model_validator(mode="after")
    def register(self) -> Self:
        if not self.is_resource and self.resource_permissions is not None:
            raise ValueError(f"resource_permissions is only allowed for Resource-based ViewSets, got it at {self!r}")

        # every construction-decidable ancestor policy constraint precedes registration (no rollback needed)
        self._validate_ancestor_policy()

        if self.pk is None:
            if self.is_resource:
                self.pk = self.model._meta.pk_type
            else:
                from django.db import models

                pk_field_map = {
                    models.UUIDField: self.PK.UUID,
                    models.AutoField: self.PK.INT,
                    models.BigAutoField: self.PK.INT,
                    models.SmallAutoField: self.PK.INT,
                    models.CharField: self.PK.STR,
                    models.SlugField: self.PK.STR,
                }
                self.pk = pk_field_map.get(type(self.model._meta.pk), self.PK.INT)

        with _REGISTRY_LOCK:
            cv_raise(
                self.name not in _REGISTRY,
                f"ViewSet name {self.name} is already registered by {_REGISTRY.get(self.name)!r}",
            )
            _REGISTRY[self.name] = self

        # ManageView is model/session tooling — not supported for Resources (spec §5.4)
        if not self.is_resource:
            base = self.get_manage_view_class()
            _AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})

        return self

    @staticmethod
    def get_viewset(name: str) -> Self:
        if name not in _REGISTRY:
            raise ViewSetNotFoundError(name)
        return _REGISTRY[name]

    @staticmethod
    def checks_all() -> Iterable[Check]:
        """
        Iterator over all checks of all viewsets
        """
        with _REGISTRY_LOCK:
            viewsets = list(_REGISTRY.values())
        for cv in viewsets:
            yield from cv.checks()

    def has_view(self, name) -> bool:
        return name in self._views

    def get_all_views(self) -> dict[str, type[CrudView]]:
        return self._views

    def checks(self) -> Iterable[Check]:
        """
        Iterator over all checks
        """
        yield CheckAttributeReg(context=self, id="E002", attribute="name", **check.REGS["name"])
        yield CheckAttributeReg(context=self, id="E003", attribute="prefix", **check.REGS["path"])
        yield CheckTemplate(context=self, id="E111", attribute="extends")
        yield from context_button_checks(self, self, self.context_buttons)

        if self.is_resource:
            from crud_views.lib.views import CreateView, DeleteView, UpdateView

            for key, view in self._views.items():
                if issubclass(view, CrudViewPermissionRequiredMixin):
                    yield CheckExpression(
                        context=view,
                        id="E260",
                        expression=view.cv_permission in self.permissions,
                        msg=(
                            f"cv_permission {view.cv_permission!r} of view {key!r} is not declared in "
                            f"resource_permissions of {self!r} — add the key or use the "
                            f"non-PermissionRequired view variant"
                        ),
                    )
                yield CheckExpression(
                    context=view,
                    id="E262",
                    expression=not issubclass(view, (CreateView, UpdateView, DeleteView)),
                    msg=(
                        f"view {key!r} is a Create/Update/Delete view — not supported for "
                        f"Resource-based ViewSets (writes need a real model, see docs)"
                    ),
                )

        # a missing parent is reported by the ancestor structure check (crud_views.checks), not as a crash here
        if self.parent is not None and self.parent.name in _REGISTRY:
            yield CheckExpression(
                context=self,
                id="E261",
                expression=not self.parent.viewset.is_resource,
                msg=(
                    f"parent ViewSet {self.parent.name!r} is Resource-based — Resources can only be "
                    f"leaves in the nesting hierarchy (v1)"
                ),
            )

        for view in self._views.values():
            yield from view.checks()

    @model_validator(mode="after")
    def model_validator_after(self) -> Self:
        if self.prefix is None:
            self.prefix = self.name
        return self

    def get_parent_url_args(self, first_only: bool = False) -> list[str] | str:
        """
        Get url args for all parents
        """
        # bounded walk (crud_views.lib.ancestors): a cycle or missing parent raises ImproperlyConfigured
        args = [edge.get_pk_name() for edge, _ in _walk_ancestors(self, first_only=first_only)]
        if first_only and args:
            return args[0]
        return args

    @property
    def has_parent(self) -> bool:
        return self.parent is not None

    def get_parent_model(self):
        if self.parent:
            return self.parent.viewset.model
        return None

    def get_parent_attributes(self, first_only: bool = False) -> list[str] | str:
        """
        Get url args for all parents
        """
        attrs = [edge.get_attribute() for edge, _ in _walk_ancestors(self, first_only=first_only)]
        if first_only and attrs:
            return attrs[0]
        return attrs

    def get_queryset(self, view: CrudView) -> QuerySet:
        """
        Queryset with respect to parent
        """
        cv_raise(
            not self.is_resource,
            f"ViewSet.get_queryset() called for Resource-based ViewSet {self!r} — "
            f"add ResourceViewMixin as the FIRST base class of the view",
        )

        q_kwargs = {}
        if self.parent:
            attribute = None
            for edge, _ancestor in _walk_ancestors(self):  # bounded: a cycle or missing parent raises
                attribute = edge.get_attribute() if attribute is None else f"{attribute}__{edge.get_attribute()}"
                q_kwargs[f"{attribute}__pk"] = view.kwargs[edge.get_pk_name()]

            queryset = self.model.objects.filter(Q(**q_kwargs))

        else:
            # default queryset
            queryset = self.model.objects.all()

        # add ordering
        if self.ordering:
            queryset = queryset.order_by(self.ordering)

        return queryset

    def register_view_class(self, key: str, view_class: type[CrudView]):
        cv_raise(key not in self._views, f"key {key} already registered at {self}")
        self._views[key] = view_class
        # add manage view to context actions; copy-on-write because the list may be
        # shared with the settings singleton or sibling view classes
        if crud_views_settings.manage_views_enabled != "no" and not self.is_resource:
            actions = view_class.cv_context_actions
            if isinstance(actions, list) and "manage" not in actions and view_class.cv_key != "manage":
                view_class.cv_context_actions = [*actions, "manage"]

    def get_manage_view_class(self) -> type[CrudView]:
        from django.utils.module_loading import import_string

        dotted = self.manage_view_class or crud_views_settings.manage_view_class
        if dotted:
            return import_string(dotted)
        return ManageView

    def is_view_registered(self, key: str) -> bool:
        return key in self._views

    def get_view_class(self, key: str) -> type[CrudView]:
        if not self.is_view_registered(key) and key == "list" and self.is_view_registered("card"):
            return self._views["card"]
        cv_raise(self.is_view_registered(key), f"key {key} not registered at {self}", ViewSetKeyFoundError)
        return self._views[key]

    def get_router_name(self, key: str) -> str:
        """
        The router name
        """
        if not self.is_view_registered(key) and key == "list" and self.is_view_registered("card"):
            key = "card"
        app = f"{self.app}:" if self.app else ""
        return f"{app}{self.name}-{key}"

    def get_view_path(self, key: str) -> str:
        return self.get_view_class(key).cv_path

    def get_view_pk_path(self, key: str) -> str:
        if self.get_view_class(key).cv_object:
            return f"/{self.pk}"
        return ""

    def get_path_parent(self) -> str:
        """
        Return path_parent of URL pattern [path_parent/]path_prefix/[path_pk/]path_view/
        """
        paths = []
        for edge, ancestor in _walk_ancestors(self):  # bounded: a cycle or missing parent raises
            path_pk = path_regs.get_path_pk(edge.get_pk_name(), ancestor.pk) + "/"
            paths.insert(0, f"{ancestor.get_path_prefix()}{path_pk}")

        path_parent = "".join(paths)
        return path_parent

    def get_path_prefix(self) -> str:
        """
        Return path_prefix of URL pattern [path_parent/]path_prefix/[path_pk/]path_view/
        """
        return f"{self.prefix}/"

    def get_path_pk(self, key: str) -> str:
        """
        Return path_pk of URL pattern [path_parent/]path_prefix/[path_pk/]path_view/
        """
        if self.get_view_class(key).cv_object:
            path_pk = path_regs.get_path_pk(self.pk_name, self.pk)
            return f"{path_pk}/"
        return ""

    def get_path_view(self, key: str) -> str:
        """
        Return path_view of URL pattern [path_parent/]path_prefix/[path_pk/]path_view/
        """
        path = self.get_view_class(key).cv_path
        if not path:
            return ""
        return f"{path}/"

    @cached_property
    def urlpatterns(self) -> list[URLResolver]:
        """
        Create urlpatterns for all views of ViewSet
        """

        # check if any views are registered
        cv_raise(len(self._views.keys()) > 0, f"no views registered at {self}")

        # URLconf import may precede system checks: the declared ancestry must be finite, resolved and free of
        # Resource ancestors before any parent path is built (ImproperlyConfigured otherwise). Relationships are
        # enforced by the ancestor system check and by the request guard before any lookup.
        if self.parent is not None:
            _validate_ancestor_structure(self, relations=False)

        urlpatterns = []

        # common path parts
        path_parent = self.get_path_parent()
        path_prefix = self.get_path_prefix()

        # create urlpatterns for all views
        for key, view_class in self._views.items():
            # view specific path parts
            path_pk = self.get_path_pk(key)
            path_view = self.get_path_view(key)
            path_contribute = view_class.cv_path_contribute()

            # args for re_path
            route = rf"^{path_parent}{path_prefix}{path_pk}{path_view}{path_contribute}$"
            view = view_class.as_view()
            name = self.get_router_name(key)

            # create and add URLResolver
            resolver = re_path(route, view, name=name)
            urlpatterns.append(resolver)

        return urlpatterns

    @property
    def default_permissions(self) -> OrderedDict[str, str]:
        """
        Default permissions extracted from model
            - add
            - change
            - delete
            - view
            - ...
            - and custom permissions defined on model

        Note: the lookup (a ``ContentType`` lookup and a ``Permission`` query) is cached for the
        process once it finds permissions; it is not refreshed if permissions change at runtime.
        An empty result is not cached: read before ``migrate`` created the rows, it would
        otherwise break every PermissionRequired view until the process restarts (#151).
        """
        if self._default_permissions is not None:
            return self._default_permissions
        cv_raise(
            not self.is_resource,
            f"default_permissions must not be used for Resource-based ViewSet {self!r}; set resource_permissions",
        )
        model = self.model
        content_type = ContentType.objects.get_for_model(model)
        permissions = OrderedDict()
        for permission in Permission.objects.filter(content_type=content_type):
            # Strip the exact terminal "_<model>" suffix through the same expression as
            # viewset.E269's static declared set.
            action = _permission_key(permission.codename, content_type.model)
            permissions[action] = f"{content_type.app_label}.{permission.codename}"
        if permissions:
            self._default_permissions = permissions
        return permissions

    def _ancestor_has_permission(self, user, permission: str, obj, *, view: CrudView) -> bool:
        """Ancestor gate of the model provider: the actor holds ``permission`` as a model permission."""
        return user.has_perm(permission)

    @property
    def permissions(self) -> OrderedDict[str, str]:
        if self.is_resource:
            return OrderedDict(self.resource_permissions or {})
        return self.default_permissions

    def get_meta(self, context: ViewContext) -> dict:
        """
        Meta data plus X for template context.
        ViewSet verbose_name* overrides win when set; resolve per call so lazy values follow the active language.
        """
        meta = self.model._meta
        verbose_name = str(self.verbose_name) if self.verbose_name is not None else meta.verbose_name
        verbose_name_plural = (
            str(self.verbose_name_plural) if self.verbose_name_plural is not None else meta.verbose_name_plural
        )
        data = {
            "viewset": self,
            "cv": self,
            "verbose_name": capfirst(verbose_name),
            "verbose_name_plural": capfirst(verbose_name_plural),
        }
        data.update(
            {
                "verbose_name_translate": _(data["verbose_name"]),
                "verbose_name_plural_translate": _(data["verbose_name_plural"]),
            }
        )
        data.update(context.to_dict())
        return data
