"""Crispy inputs whose CSS classes come from the layered button class table."""

from crispy_forms import layout

from crud_views.lib.button_classes import get_button_class


class _TableClassMixin:
    """
    Sets the crispy ``field_classes`` of the instance from the button class table, before crispy
    appends a project supplied ``css_class``. ``slot`` (``"location:slot"``) picks the table key.
    """

    slot: str

    def __init__(self, name, value, *, slot: str | None = None, **kwargs):
        self.field_classes = get_button_class(*(slot or self.slot).split(":", 1))
        super().__init__(name, value, **kwargs)


class Submit(_TableClassMixin, layout.Submit):
    slot = "form:submit"


class Button(_TableClassMixin, layout.Button):
    slot = "form:cancel"


class Reset(_TableClassMixin, layout.Reset):
    slot = "form:filter-reset"
