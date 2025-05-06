from pydantic import BaseModel


class Tab(BaseModel, arbitrary_types_allowed=True):
    name: str   # todo: rename to key
    label: str | None = None
    label_tooltip: str | None = None
    property_group_name: str | None = None
    template_name: str | None = None
    selected: bool = False
    table: str | None = None
    icon: str | None = None

    def __hash__(self):
        return hash(f"{self.name}-{self.label}")

    @property
    def label_display(self) -> str:
        return self.label or self.name.capitalize()

