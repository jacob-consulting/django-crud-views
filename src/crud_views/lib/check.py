import re
from typing import Any, Iterable, Type

from django.core.checks import Error, CheckMessage
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
        if self.exists and not self.reg.match(self.value):
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


class ContextActionCheck(Check):
    """
    Checks for context action

    A ``cv_context_actions`` entry resolves either to a sibling view registered on the
    ViewSet (``ViewSet.has_view``) or to a context button (view-level ``cv_context_buttons``
    or viewset-level ``context_buttons``, e.g. "home", "parent", "filter") — mirroring the
    two-path resolution performed at render time by ``CrudView.cv_get_context()``. Only
    actions resolving to neither are misconfigurations.

    ``cv_viewset`` may legitimately be unset (e.g. isolated check-only test view classes not
    wired to a real ViewSet); in that case there is nothing to validate against, so no
    message is emitted.
    """

    id: str = "E203"
    msg: str = "Context action »{action}» does not resolve to a view or context button in the viewset at »{context}»"

    def messages(self) -> Iterable[CheckMessage]:
        viewset = getattr(self.context, "cv_viewset", None)
        if viewset is None:
            return
        actions = self.context.cv_context_actions or list()
        button_keys = {cb.key for cb in getattr(self.context, "cv_context_buttons", None) or []}
        button_keys |= {cb.key for cb in getattr(viewset, "context_buttons", None) or []}
        for action in actions:
            if action in button_keys:
                continue
            if not viewset.has_view(action):
                yield Error(id=self.get_id(), msg=self.msg.format(action=action, context=self.context))


class CheckExpression(Check):
    expression: bool
    msg: str = "foo"

    def messages(self) -> Iterable[CheckMessage]:
        if not self.expression:
            yield Error(id=f"viewset.{self.id}", msg=f"{self.msg} at {self.context}")
