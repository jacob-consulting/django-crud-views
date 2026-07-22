import difflib
import re
from typing import Any, Iterable, Type

from django.core.checks import Error, CheckMessage
from django.core.checks import Warning as DjangoWarning
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from pydantic import BaseModel

REGS = {
    "name": {
        "reg": re.compile(r"^[a-z][a-z0-9_]*$"),
        "msg": "must be lowercase alpha with underscores, digits allowed after the first character",
    },
    "path": {
        "reg": re.compile(r"^$|^[a-z0-9_-]+(?:/[a-z0-9_-]+)*$"),
        "msg": "must be lowercase alpha with underscores and dashes and must not start or end with a slash",
    },
}


class Check(BaseModel):
    """
    Base class for checks
    """

    context: Type | object
    id: str
    msg: str | None = None

    def get_id(self) -> str:
        """
        error id
        """
        return f"viewset.{self.id}"

    def get_message_context(self) -> dict:
        return dict(
            context=self.context,
            id=self.id,
            eid=self.get_id(),
        )

    def get_message(self, msg: str = None) -> str:
        kwargs = self.get_message_context()
        template = msg if msg else self.msg
        return template.format(**kwargs)


class CheckAttribute(Check):
    """
    Check for attribute
    """

    id: str = "E100"
    attribute: str | None = None
    nullable: bool = False
    msg: str = "Attribute »{attribute}» does not exist or is not set at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(
            attribute=self.attribute,
            value=self.value,
        )
        return context

    @property
    def exists(self) -> bool:
        return hasattr(self.context, self.attribute)

    @property
    def value(self) -> Any:
        return getattr(self.context, self.attribute)

    def messages(self) -> Iterable[CheckMessage]:
        if not self.exists or (self.value is None and not self.nullable):
            yield Error(id=self.get_id(), msg=self.get_message())


class CheckAttributeReg(CheckAttribute):
    """
    Check attribute against regex
    """

    reg: re.Pattern
    msg: str = "Attribute »{attribute}» value »{value}» does not match regex »{reg}» at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(
            reg=self.reg,
        )
        return context

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()
        if self.exists and self.value is not None and not self.reg.match(self.value):
            yield Error(id=f"viewset.{self.id}", msg=self.get_message())


class CheckAttributeType(CheckAttribute):
    """
    Check attribute value is an instance of the expected type
    """

    id: str = "E101"
    expected_type: type | tuple[type, ...]
    msg: str = "Attribute »{attribute}» value »{value}» is not of type »{expected_type}» at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(expected_type=self.expected_type)
        return context

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()
        if self.exists and self.value is not None and not isinstance(self.value, self.expected_type):
            yield Error(id=self.get_id(), msg=self.get_message())


class CheckMapping(CheckAttribute):
    """
    Check attribute is a dict mapping keys (subclasses of key_type) to values (instances of value_type)
    """

    id: str = "E205"
    key_type: type | tuple[type, ...]
    value_type: type | tuple[type, ...]
    msg: str = "Attribute »{attribute}» at »{context}» is not a valid mapping: {detail}"

    def _error(self, detail: str) -> Error:
        kwargs = self.get_message_context()
        return Error(id=self.get_id(), msg=self.msg.format(detail=detail, **kwargs))

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()
        if not self.exists or self.value is None:
            return
        value = self.value
        if not isinstance(value, dict):
            yield self._error(f"expected a dict, got {type(value).__name__}")
            return
        for key, val in value.items():
            if not isinstance(key, type) or not issubclass(key, self.key_type):
                yield self._error(f"key »{key!r}» is not a subclass of {self.key_type}")
            if not isinstance(val, self.value_type):
                yield self._error(f"value for »{key!r}» is not of type {self.value_type}")


class CheckEitherAttribute(Check):
    """
    Check for either attribute
    """

    attribute1: str | None = None
    attribute2: str | None = None
    allow_none: bool = False

    msg: str = "Neither »{attribute1}» nor »{attribute2}» are set or are missing »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(
            attribute1=self.attribute1,
            attribute2=self.attribute2,
            value1=self.value1,
            value2=self.value2,
        )
        return context

    @property
    def value1(self) -> Any:
        return getattr(self.context, self.attribute1, None)

    @property
    def value2(self) -> Any:
        return getattr(self.context, self.attribute2, None)

    def messages(self) -> Iterable[CheckMessage]:
        if not self.value1 and not self.value2 and not self.allow_none:
            yield Error(
                id=self.get_id(),
                msg=self.get_message(
                    "Neither attribute »{attribute1}» nor attribute »{attribute2}» are set at »{context}»"
                ),
            )

        elif self.value1 and self.value2:
            yield Error(
                id=self.get_id(),
                msg=self.get_message("Both attributes »{attribute1}» and »{attribute2}» are set at »{context}»"),
            )


class CheckTemplateOrCode(Check):
    """
    Check for template or template_code
    """

    id: str = "E110"
    attribute: str | None = None
    msg_none: str = "Neither »{attr_template}» nor »{attr_code}» defined at »{context}»"
    msg_template_not_found: str = "Template »{template}» not found at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(
            attribute=self.attribute,
        )
        return context

    def messages(self) -> Iterable[CheckMessage]:
        attr_template = f"{self.attribute}"
        attr_code = f"{self.attribute}_code"
        template = getattr(self.context, attr_template, None)
        code = getattr(self.context, attr_code, None)
        if not (template or code):
            msg = self.msg_none.format(attr_template=attr_template, attr_code=attr_code, context=self.context)
            yield Error(id=self.get_id(), msg=msg)
        if template:
            try:
                get_template(template)
            except TemplateDoesNotExist:
                msg = self.msg_template_not_found.format(template=template, context=self.context)
                yield Error(id=self.get_id(), msg=msg)


class CheckTemplate(Check):
    """
    Validate that an optional template attribute, if set, resolves.

    Unlike CheckTemplateOrCode this emits no error when the attribute is unset —
    it only guards against a configured-but-missing template (e.g. an overridden
    cv_extends_template or a ViewSet extends).
    """

    id: str = "E111"
    attribute: str  # required — getattr(context, None) would raise
    msg_template_not_found: str = "Template »{template}» not found at »{context}»"

    def messages(self) -> Iterable[CheckMessage]:
        template = getattr(self.context, self.attribute, None)
        if template:
            try:
                get_template(template)
            except TemplateDoesNotExist:
                msg = self.msg_template_not_found.format(template=template, context=self.context)
                yield Error(id=self.get_id(), msg=msg)


class CheckExpression(Check):
    expression: bool
    msg: str = "foo"

    def messages(self) -> Iterable[CheckMessage]:
        if not self.expression:
            yield Error(id=f"viewset.{self.id}", msg=f"{self.msg} at {self.context}")


_PACKAGE_PREFIX = "crud_views"
_CV_PREFIX = "cv_"
_IGNORE_ATTR = "cv_check_ignore_attributes"


def _is_config_value(value: Any) -> bool:
    """True for a plain data attribute — not a method, property, classmethod, or other descriptor."""
    return not (callable(value) or hasattr(value, "__get__"))


def _own_cv_annotations(klass: type) -> set[str]:
    """cv_*-prefixed names annotated on this class only (own annotations, no inheritance).

    Handles annotation-only declarations like `cv_formsets: FormSets` (no default) that
    never appear in vars(klass). `klass.__annotations__` returns the class's own annotations
    (empty dict if none) on Python 3.10+; wrapped defensively for the PEP 649 lazy path on 3.14.
    """
    try:
        annotations = klass.__annotations__
    except Exception:
        annotations = vars(klass).get("__annotations__", {})
    return {name for name in annotations if name.startswith(_CV_PREFIX)}


def _collect_cv_names(klass: type, all_names: set[str], data_names: set[str]) -> None:
    """Add klass's own cv_* declarations — defaults (vars) and annotation-only — to the sets."""
    for name in _own_cv_annotations(klass):
        all_names.add(name)
        data_names.add(name)  # annotation-only config attrs are data, suggestible
    for name, value in vars(klass).items():
        if name.startswith(_CV_PREFIX):
            all_names.add(name)
            if _is_config_value(value):
                data_names.add(name)


def _registered_view_classes() -> list[type]:
    """All view classes across every registered ViewSet (empty before the app registry loads)."""
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())
    classes: list[type] = []
    for viewset in viewsets:
        classes.extend(viewset.get_all_views().values())
    return classes


_VOCAB_CACHE: dict[int, tuple[frozenset[str], frozenset[str]]] = {}


def _registry_vocabulary() -> tuple[frozenset[str], frozenset[str]]:
    """Package-wide (all cv_* names, data-attribute cv_* names) declared by any crud_views* class
    used by a registered view. Cached per registry size — the ViewSet registry only grows at
    import time and is stable when system checks run, so the count is a safe cache key."""
    classes = _registered_view_classes()
    key = len(classes)
    cached = _VOCAB_CACHE.get(key)
    if cached is not None:
        return cached
    all_names: set[str] = set()
    data_names: set[str] = set()
    seen: set[type] = set()
    for view in classes:
        for klass in view.__mro__:
            if klass in seen or not klass.__module__.startswith(_PACKAGE_PREFIX):
                continue
            seen.add(klass)
            _collect_cv_names(klass, all_names, data_names)
    result = (frozenset(all_names), frozenset(data_names))
    _VOCAB_CACHE[key] = result
    return result


class CheckUnknownAttributes(Check):
    """
    Warn about cv_* data attributes that no crud_views class declares.

    A typo or stale name (cv_message for cv_message_template_code, an attribute
    removed in a rename) is otherwise silently ignored. The known-set is derived
    from the MRO: every legitimate config attribute is declared with a default on
    a crud_views* class, so no hand-maintained registry is needed. Only non-callable,
    non-descriptor data attributes are flagged (user cv_* methods/properties are skipped).
    """

    id: str = "W280"
    msg: str = (
        "{attribute} on {context} is not a known crud_views attribute — it is silently "
        "ignored (dead attribute or typo).{suggestion}"
    )

    def _context_names(self) -> tuple[set[str], set[str]]:
        """(all cv_* names, data-attribute cv_* names) declared by crud_views* classes in this
        view's own MRO. The data subset is the suggestion pool — kept context-local so a
        'did you mean' hint stays relevant to this view type instead of pulling in unrelated
        attributes (e.g. cv_action_messages from ActionView) via the package-wide set."""
        all_names: set[str] = set()
        data_names: set[str] = set()
        for klass in self.context.__mro__:
            if klass.__module__.startswith(_PACKAGE_PREFIX):
                _collect_cv_names(klass, all_names, data_names)
        return all_names, data_names

    def _allowlist(self) -> set[str]:
        # union across the MRO so a mixin and the leaf view can each exempt their own attrs
        allow: set[str] = set()
        for klass in self.context.__mro__:
            value = vars(klass).get(_IGNORE_ATTR)
            if value:
                allow.update(value)
        return allow

    def _suspects(self) -> set[str]:
        suspects: set[str] = set()
        for klass in self.context.__mro__:
            if klass.__module__.startswith(_PACKAGE_PREFIX):
                continue  # package code defines the known-set, never suspect
            for name, value in vars(klass).items():
                if name.startswith(_CV_PREFIX) and _is_config_value(value):
                    suspects.add(name)
        return suspects

    def _suggestion(self, name: str, pool: set[str]) -> str:
        # pool is the data-attribute known-set — suggest real config attributes, never methods
        candidates = sorted(pool)
        matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
        if not matches:
            # difflib misses when the correct name is much longer; fall back to prefix
            prefixed = sorted((k for k in candidates if k.startswith(name)), key=len)
            matches = prefixed[:1]
        return f" Did you mean {matches[0]}?" if matches else ""

    def messages(self) -> Iterable[CheckMessage]:
        reg_all, _reg_data = _registry_vocabulary()
        ctx_all, ctx_data = self._context_names()
        known_all = reg_all | ctx_all  # package-wide: is this a real crud_views attribute name?
        unknown = self._suspects() - known_all - self._allowlist()
        for name in sorted(unknown):
            # suggest only from THIS view's own data attributes, so the hint stays relevant
            suggestion = self._suggestion(name, ctx_data)
            msg = self.msg.format(attribute=name, context=self.context, suggestion=suggestion)
            yield DjangoWarning(
                msg,
                hint=(
                    f"Remove it, fix the name, or add it to {_IGNORE_ATTR} on the view "
                    f"if it is an intentional custom attribute."
                ),
                id=self.get_id(),
            )
