import threading
from collections import OrderedDict
from functools import cached_property
from typing import Dict, List, Type, Any, Iterable, ClassVar

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet, Q
from django.urls import re_path, URLResolver
from django.utils.translation import gettext as _
from pydantic import BaseModel, PrivateAttr, Field, model_validator
from typing_extensions import Self

from crud_views.lib.exceptions import cv_raise, ViewSetNotFoundError, ViewSetKeyFoundError
from crud_views.lib.viewset import path_regs
from .parentviewset import ParentViewSet
from .path_regs import PrimaryKeys
from .. import check
from ..check import CheckAttributeReg, Check
from ..settings import crud_views_settings
from ..view import ContextButton, ParentContextButton, CrudView, ViewContext, CrudViewPermissionRequiredMixin
from ..view.buttons import FilterContextButton
from ..views.manage import ManageView

User = get_user_model()


def empty_dict() -> dict:
    return dict()


def context_buttons_default(*args, **kwargs) -> Any:
    return [
        ContextButton(
            key="home",
            key_target="list",
            # I don't think we need templates here because the title should be the one of the list page where it links to
        ),
        ParentContextButton(key="parent", key_target="list"),
        FilterContextButton(),
    ]


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

    PK: ClassVar[Type[PrimaryKeys]] = PrimaryKeys

    model: Type[Model]
    name: str
    prefix: str | None = None
    app: str | None = None
    pk: str = PK.INT     # todo: better name
    pk_name: str = "pk"
    context_buttons: List[ContextButton] = Field(default_factory=context_buttons_default)
    parent: ParentViewSet | None = None
    ordering: str | None = None
    icon_header: str | None = None

    _views: Dict[str, Type[CrudView]] = PrivateAttr(default_factory=empty_dict)  # noqa

    def __repr__(self):
        return f"ViewSet({self.name})"

    def __str__(self):
        return f"{self.name}"

    @model_validator(mode='after')
    def register(self) -> Self:
        with _REGISTRY_LOCK:
            _REGISTRY[self.name] = self

        switch = crud_views_settings.manage_views_enabled
        if switch == "yes" or switch == "debug_only" and settings.DEBUG:
            class AutoManageView(ManageView):
                model = self.model
                cv_viewset = self

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
            for cv in _REGISTRY.values():
                yield from cv.checks()

    def has_view(self, name) -> bool:
        return name in self._views

    def get_all_views(self) -> Dict[str, Type[CrudView]]:
        return self._views

    def checks(self) -> Iterable[Check]:
        """
        Iterator over all checks
        """
        yield CheckAttributeReg(context=self, id="E002", attribute="name", **check.REGS["name"])
        yield CheckAttributeReg(context=self, id="E003", attribute="prefix", **check.REGS["path"])

        for view in self._views.values():
            yield from view.checks()


    @model_validator(mode='after')
    def model_validator_after(self) -> Self:
        if self.prefix is None:
            self.prefix = self.name
        return self

    def get_parent_url_args(self, first_only: bool = False) -> List[str] | str:
        """
        Get url args for all parents
        """
        args = []

        # iterate over parents
        if self.parent:
            parent = self.parent
            while parent is not None:
                arg = parent.get_pk_name()
                if first_only:
                    return arg
                args.append(parent.get_pk_name())
                parent = parent.viewset.parent

        return args

    @property
    def has_parent(self) -> bool:
        return self.parent is not None

    def get_parent_model(self):
        if self.parent:
            return self.parent.viewset.model
        return None

    def get_parent_attributes(self, first_only: bool = False) -> List[str] | str:
        """
        Get url args for all parents
        """
        attrs = []

        # iterate over parents
        if self.parent:
            parent = self.parent
            while parent is not None:
                attr = parent.get_attribute()
                if first_only:
                    return attr
                attrs.append(parent.get_attribute())
                parent = parent.viewset.parent

        return attrs

    def get_queryset(self, view: CrudView) -> QuerySet:
        """
        Queryset with respect to parent
        """

        q_kwargs = dict()
        if self.parent:
            parent = self.parent
            attribute = None
            while parent is not None:

                # parent args
                pk_name = parent.get_pk_name()
                if attribute is None:
                    attribute = parent.get_attribute()
                else:
                    attribute = f"{attribute}__{parent.get_attribute()}"

                # generate q-args
                q_kwargs.update({f"{attribute}__pk": view.kwargs[pk_name]})

                # proceed to next parent
                parent = parent.viewset.parent

            queryset = self.model.objects.filter(Q(**q_kwargs))

        else:
            # default queryset
            queryset = self.model.objects.all()

        # add ordering
        if self.ordering:
            queryset = queryset.order_by(self.ordering)

        return queryset

    def register_view_class(self, key: str, view_class: Type[CrudView]):
        cv_raise(key not in self._views, f"key {key} already registered at {self}")
        self._views[key] = view_class
        # add manage view to context
        if True:  # todo: based on settings
            if isinstance(view_class.cv_context_actions, list):
                if "manage" not in view_class.cv_context_actions and view_class.cv_key != "manage":
                    view_class.cv_context_actions.append("manage")

    def is_view_registered(self, key: str) -> bool:
        return key in self._views

    def get_view_class(self, key: str) -> Type[CrudView]:
        cv_raise(self.is_view_registered(key), f"key {key} not registered at {self}", ViewSetKeyFoundError)
        return self._views[key]

    def get_router_name(self, key: str) -> str:
        """
        The router name
        """
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

        parent = self.parent
        while parent:
            path_prefix = parent.viewset.get_path_prefix()
            path_pk = path_regs.get_path_pk(parent.get_pk_name(), parent.viewset.pk) + "/"
            path = f"{path_prefix}{path_pk}"
            paths.insert(0, path)
            parent = parent.viewset.parent

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
    def urlpatterns(self) -> List[URLResolver]:
        """
        Create urlpatterns for all views of ViewSet
        """

        # check if any views are registered
        cv_raise(len(self._views.keys()) > 0, f"no views registered at {self}")

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
            route = fr"^{path_parent}{path_prefix}{path_pk}{path_view}{path_contribute}$"
            view = view_class.as_view()  # noqa
            name = self.get_router_name(key)

            # create and add URLResolver
            resolver = re_path(route, view, name=name)
            urlpatterns.append(resolver)

        return urlpatterns

    @cached_property
    def default_permissions(self) -> OrderedDict[str, str]:
        """
        Default permissions extracted from model
            - add
            - change
            - delete
            - view
            - ...
            - and custom permissions defined on model
        """
        model = self.model  # noqa
        content_type = ContentType.objects.get_for_model(model)
        permissions = OrderedDict()
        for permission in Permission.objects.filter(content_type=content_type):
            # todo: model name must in codename
            action = permission.codename.split(f"_{permission.content_type.model}")[0]
            permissions[action] = f"{permission.content_type.app_label}.{permission.codename}"
        return permissions

    @cached_property
    def permissions(self) -> OrderedDict[str, str]:
        # todo: move to view ?
        return self.default_permissions

    def get_meta(self, context: ViewContext) -> dict:
        """
        Meta data plus X for template context.
        """
        meta = self.model._meta
        data = {
            "viewset": self,
            "cv": self,
            "verbose_name": meta.verbose_name.capitalize(),
            "verbose_name_plural": meta.verbose_name_plural.capitalize()
        }
        data.update({
            "verbose_name_translate": _(data["verbose_name"]),
            "verbose_name_plural_translate": _(data["verbose_name_plural"])
        })
        data.update(context.to_dict())
        return data
