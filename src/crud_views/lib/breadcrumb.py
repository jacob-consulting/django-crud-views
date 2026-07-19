"""
Breadcrumb support for CrudViews.

BreadcrumbItem/Breadcrumb are late-resolving: items carry a URL pattern *name* plus
args/kwargs and are resolved to concrete URLs only when rendered.
"""

from typing import Any, Dict, List, Tuple

from django.urls import reverse
from pydantic import BaseModel, field_validator, model_validator


class BreadcrumbItem(BaseModel):
    title: str
    url_name: str | None = None  # Django URL pattern name, resolved late via reverse()
    args: tuple = ()
    kwargs: dict = {}

    @field_validator("title", mode="before")
    @classmethod
    def coerce_title(cls, value: Any) -> str:
        # accept gettext_lazy promises
        return str(value)

    @model_validator(mode="after")
    def check_url_arguments(self) -> "BreadcrumbItem":
        if self.url_name is None:
            self.args = ()
            self.kwargs = {}
        elif self.args and self.kwargs:
            raise ValueError("BreadcrumbItem accepts args or kwargs, not both (reverse() restriction)")
        return self

    def resolve(self) -> Dict[str, str | None]:
        if self.url_name is None:
            url = None
        else:
            url = reverse(self.url_name, args=self.args or None, kwargs=self.kwargs or None)
        return {"title": self.title, "url": url}


class Breadcrumb(BaseModel):
    items: Tuple[BreadcrumbItem, ...] = ()

    def resolve_items(self) -> List[Dict[str, str | None]]:
        return [item.resolve() for item in self.items]
