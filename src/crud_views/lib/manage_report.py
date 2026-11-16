"""Versioned manage diagnostics: representation only, never configuration evaluation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WireModel(BaseModel):
    # Consumers tolerate additive fields. Known fields never accept coercion.
    model_config = ConfigDict(strict=True, allow_inf_nan=False)


class Selection(WireModel):
    viewset: str | None = None
    view: str | None = None
    user: str | None = None


class ReportError(WireModel):
    code: Literal[
        "invalid_arguments",
        "unknown_viewset",
        "unknown_view",
        "unknown_user",
        "collection_failed",
        "output_validation_failed",
    ]
    section: str | None = None
    message: str
    exception_class: str | None = None
    location: list[str | int] = Field(default_factory=list)


class Identity(WireModel):
    name: str
    kind: Literal["model", "guardian", "resource"]
    backing_class: str
    parent: str | None


class CatalogueEntry(Identity):
    views: list[str]


class CatalogueData(WireModel):
    entries: list[CatalogueEntry]


class CatalogueResult(WireModel):
    version: Literal[1] = 1
    kind: Literal["catalogue"] = "catalogue"
    status: Literal["complete", "partial", "failed"]
    selection: Selection
    data: CatalogueData | None
    errors: list[ReportError] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_result(self):
        if self.status == "complete" and (self.data is None or self.errors):
            raise ValueError("Complete reports require data and no collection errors")
        if self.status == "failed" and (self.data is not None or not self.errors):
            raise ValueError("Failed reports require errors and no data")
        if self.status == "partial" and (self.data is None or not self.errors):
            raise ValueError("Partial reports require surviving data and errors")
        return self
