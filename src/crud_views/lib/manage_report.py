"""Versioned manage diagnostics: representation only, never configuration evaluation."""

import math
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from django.utils.translation import gettext_lazy, pgettext_lazy
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator
from typing_extensions import TypeAliasType  # noqa: UP035 - Pydantic 2.2 recognizes the backported alias.

JsonValue = TypeAliasType(  # noqa: UP040 - retain Pydantic 2.2 compatibility.
    "JsonValue", "bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None"
)
SectionKey = Literal[
    "facts", "presentation", "views", "routes", "hierarchy", "ancestor_policy", "permissions", "checks", "guardian"
]


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
    section: SectionKey | None = None
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


class Normalization(WireModel):
    path: list[str | int]
    python_type: str


class ValueRecord(WireModel):
    kind: Literal["native", "class_path", "unsupported", "not_declared"]
    value: JsonValue = None
    python_type: str | None = None
    normalizations: list[Normalization] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_value(self):
        if self.kind == "class_path" and not isinstance(self.value, str):
            raise ValueError("Class paths must be strings")
        if self.kind in {"unsupported", "not_declared"} and self.value is not None:
            raise ValueError("Unavailable values cannot contain data")
        return self


class SourceRecord(WireModel):
    code: Literal[
        "default",
        "set",
        "inherited",
        "viewset",
        "global_setting",
        "model_meta",
        "resource_meta",
        "fixed",
        "not_declared",
        "effective",
    ]
    setting: str | None = None
    declaring_class: str | None = None


def normalize_value(value, *, not_declared=False, _projection=None):
    """Bounded JSON projection; no arbitrary instance formatting or traversal."""
    if not_declared:
        return ValueRecord(kind="not_declared")
    python_type = f"{type(value).__module__}.{type(value).__qualname__}"
    if isinstance(value, type):
        return ValueRecord(kind="class_path", value=f"{value.__module__}.{value.__qualname__}", python_type=python_type)
    markers, active = [], set()
    translation_types = (type(gettext_lazy("")), type(pgettext_lazy("", "")))

    def project(item, path):
        if item is None or type(item) in (bool, int, str):
            return item
        if type(item) is float and math.isfinite(item):
            return item
        if type(item) in translation_types:
            # Only the two exact Django wrappers with ordinary string arguments.
            # A Promise subclass, arbitrary lazy(), or a wrapped object can execute
            # project code even though it presents itself as a translation string.
            args, kwargs = item._args, item._kw
            if type(args) is not tuple or type(kwargs) is not dict:
                raise ValueError("unsupported translation arguments")
            if any(type(arg) is not str for arg in args) or any(
                type(key) is not str or type(arg) is not str for key, arg in kwargs.items()
            ):
                raise ValueError("unsupported translation arguments")
            return str(item)
        projected = _projection(item) if _projection is not None else None
        if projected is not None:
            if id(item) in active:
                raise ValueError("cyclic projection")
            active.add(id(item))
            markers.append(Normalization(path=path, python_type=f"{type(item).__module__}.{type(item).__qualname__}"))
            try:
                return project(projected, path)
            finally:
                active.remove(id(item))
        if type(item) not in (list, tuple, dict) or id(item) in active:
            raise ValueError("unsupported configuration value")
        active.add(id(item))
        try:
            if type(item) is dict:
                if any(type(key) is not str for key in item):
                    raise ValueError("non-string mapping key")
                return {key: project(child, [*path, key]) for key, child in item.items()}
            if type(item) is tuple:
                markers.append(Normalization(path=path, python_type="builtins.tuple"))
            return [project(child, [*path, index]) for index, child in enumerate(item)]
        finally:
            active.remove(id(item))

    try:
        projected = project(value, [])
    except (ValueError, RecursionError):
        return ValueRecord(kind="unsupported", python_type=python_type)
    return ValueRecord(
        kind="native", value=projected, python_type=python_type if markers else None, normalizations=markers
    )


class ConfigEntry(WireModel):
    key: str
    value: ValueRecord
    source: SourceRecord
    is_default: bool
    unknown: bool | None = None
    declared_value: ValueRecord | None = None
    icon: str | None = None
    type: str | None = None
    is_button: bool | None = None
    empty_buttons: bool | None = None
    points_to: str | None = None
    label: str | None = None


class ConfigGroup(WireModel):
    key: str
    label: str
    entries: list[ConfigEntry]
    default_count: int


class FactsData(WireModel):
    scope: Literal["viewset"] = "viewset"
    entries: list[ConfigEntry]


class PresentationData(WireModel):
    scope: Literal["viewset"] = "viewset"
    sections: list[ConfigGroup]
    default_count: int
    set_count: int


class Requirement(WireModel):
    kind: Literal["permission", "group", "none", "custom"]
    value: str | None
    ancestor_applies: bool


class ParentRequirement(WireModel):
    key: str
    permission: str | None


class ViewPolicy(WireModel):
    applicable: bool
    accept_global_perms: bool | None
    effective_policy: Literal["strict", "global_fallback", "not_applicable"]
    tooltip: str


class ViewRow(WireModel):
    key: str
    route_name: str
    route: str | None
    route_error: str | None
    class_path: str
    requirement: Requirement
    permission: str | None
    parent_requirement: ParentRequirement | None
    requirement_metadata_error: str | None
    guardian_policy: ViewPolicy | None
    parent_only_requirement: bool | None = None
    sections: list[ConfigGroup]


class ViewsData(WireModel):
    scope: Literal["viewset", "selected_view"] = "viewset"
    selected_view: str | None = None
    entries: list[ViewRow]


class RouteRow(WireModel):
    key: str
    name: str
    route: str | None
    route_error: str | None


class RoutesData(WireModel):
    scope: Literal["viewset", "selected_view"] = "viewset"
    selected_view: str | None = None
    entries: list[RouteRow]


class HierarchyItem(WireModel):
    name: str
    model: str
    resource: bool
    route_name: str | None
    route: str | None
    route_error: str | None
    url: str | None


class HierarchyData(WireModel):
    scope: Literal["viewset"] = "viewset"
    parents: list[HierarchyItem]
    children: list[HierarchyItem]
    route_error: str | None


class AncestorPair(WireModel):
    nearest: str
    higher: str


PolicyT = TypeVar("PolicyT")


class PolicyValue(WireModel, Generic[PolicyT]):  # noqa: UP046 - Pydantic 2.2 generic syntax.
    declared: PolicyT | None
    effective: PolicyT


class AsAncestor(WireModel):
    provider: Literal["model", "guardian", "none"] | None
    effective_provider: Literal["model", "guardian", "none"]
    accept_global_perms: bool


class AncestorRequests(WireModel):
    cascade: PolicyValue[bool]
    read: PolicyValue[AncestorPair]
    write: PolicyValue[AncestorPair]
    actions: dict[str, AncestorPair]


class AncestorPolicyData(WireModel):
    scope: Literal["viewset"] = "viewset"
    as_ancestor: AsAncestor
    requests: AncestorRequests | None


class PermissionColumn(WireModel):
    key: str
    permission: str
    codename: str


class PermissionCell(WireModel):
    key: str
    model: bool
    object_count: int | None


class HolderRow(WireModel):
    id: int | str
    label: str
    member_count: int | None
    cells: list[PermissionCell]


class ActorSelection(WireModel):
    state: Literal["not_selected", "selected"]
    row: HolderRow | None

    @model_validator(mode="after")
    def coherent_actor(self):
        if (self.state == "selected") != (self.row is not None):
            raise ValueError("Actor selection and row must agree")
        return self


class Superusers(WireModel):
    count: int
    names: list[str] | None
    meaning: Literal["global_grants", "global_grants_not_strict_object_helper"]


class PermissionsData(WireModel):
    scope: Literal["viewset"] = "viewset"
    columns: list[PermissionColumn]
    grant_kind: Literal["model", "resource"]
    actor: ActorSelection
    groups: list[HolderRow]
    holder_visibility: Literal["hidden", "shown"]
    users: list[HolderRow] | None
    superusers: Superusers


class CheckMessage(WireModel):
    id: str | None
    severity: str
    level: int
    severity_code: Literal["debug", "info", "warning", "error", "critical", "unknown"]
    message: str
    hint: str | None


class ChecksData(WireModel):
    scope: Literal["viewset"] = "viewset"
    count: int
    messages: list[CheckMessage]


class GuardianHelper(WireModel):
    policy: str
    accept_global_perms: bool
    use_groups: bool


class GuardianData(WireModel):
    scope: Literal["viewset"] = "viewset"
    get_objects_for_user: GuardianHelper


SectionT = TypeVar("SectionT")


class Section(WireModel, Generic[SectionT]):  # noqa: UP046 - Pydantic 2.2 generic syntax.
    status: Literal["ok", "error", "not_applicable"]
    data: SectionT | None
    errors: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_section(self):
        if (self.status == "ok") != (self.data is not None):
            raise ValueError("Only successful sections contain data")
        if (self.status == "error") != bool(self.errors):
            raise ValueError("Only failed sections reference errors")
        return self


class InspectionData(WireModel):
    identity: Identity
    facts: Section[FactsData]
    presentation: Section[PresentationData]
    views: Section[ViewsData]
    routes: Section[RoutesData]
    hierarchy: Section[HierarchyData]
    ancestor_policy: Section[AncestorPolicyData]
    permissions: Section[PermissionsData]
    checks: Section[ChecksData]
    guardian: Section[GuardianData]


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


class InspectionResult(CatalogueResult):
    kind: Literal["inspection"] = "inspection"
    data: InspectionData | None

    @model_validator(mode="after")
    def coherent_sections(self):
        if self.data is not None:
            useful = False
            for name in InspectionData.model_fields:
                if name == "identity":
                    continue
                section = getattr(self.data, name)
                useful |= section.status == "ok"
                for index in section.errors:
                    if not 0 <= index < len(self.errors) or self.errors[index].section != name:
                        raise ValueError("Invalid section error reference")
            if self.status == "partial" and not useful:
                raise ValueError("Partial reports require a useful surviving section")
        return self


Report = TypeAdapter(Annotated[CatalogueResult | InspectionResult, Field(discriminator="kind")])


def report_schema():
    return Report.json_schema(mode="serialization")


def _entry(row):
    metadata = row["_export"]  # Missing complete values are unavailable, never reconstructed from display text.
    return ConfigEntry.model_validate({**row, **metadata})


def _group(group):
    return ConfigGroup.model_validate({**group, "entries": [_entry(row) for row in group["entries"]]})


def _holder(row):
    return HolderRow.model_validate({**row, "id": str(row["id"]) if isinstance(row["id"], UUID) else row["id"]})


def adapt_section(name, raw, *, kind="model", selected_view=None):
    """Project documented builder shapes; validation rejects malformed known fields."""
    if name == "facts":
        return FactsData(entries=[_entry(row) for row in raw])
    if name == "presentation":
        return PresentationData.model_validate({**raw, "sections": [_group(group) for group in raw["sections"]]})
    if name == "views":
        rows = [
            ViewRow.model_validate({**row, "sections": [_group(group) for group in row["sections"]]})
            for row in raw
            if selected_view is None or row["key"] == selected_view
        ]
        return ViewsData(
            entries=rows, selected_view=selected_view, scope="selected_view" if selected_view else "viewset"
        )
    if name == "routes":
        return RoutesData(
            entries=[row for row in raw if selected_view is None or row["key"] == selected_view],
            selected_view=selected_view,
            scope="selected_view" if selected_view else "viewset",
        )
    if name == "hierarchy":
        return HierarchyData.model_validate(raw)
    if name == "ancestor_policy":
        return AncestorPolicyData.model_validate(raw)
    if name == "checks":
        return ChecksData.model_validate(raw)
    if name == "guardian":
        return GuardianData.model_validate(raw)
    if name == "permissions":
        # Validate the visibility flag before using it as a branch condition.
        if type(raw["show_users"]) is not bool:
            raise ValueError("show_users must be a boolean")
        shown = raw["show_users"]
        actor = raw["actor"]
        return PermissionsData(
            columns=raw["columns"],
            grant_kind="resource" if kind == "resource" else "model",
            actor=ActorSelection(
                state="selected" if actor is not None else "not_selected",
                row=_holder(actor) if actor is not None else None,
            ),
            groups=[_holder(row) for row in raw["groups"]],
            holder_visibility="shown" if shown else "hidden",
            users=[_holder(row) for row in raw["users"] + raw["users_overflow"]] if shown else None,
            superusers=Superusers(
                count=raw["superusers"]["count"],
                names=raw["superusers"]["names"] if shown else None,
                meaning="global_grants_not_strict_object_helper" if kind == "guardian" else "global_grants",
            ),
        )
    raise ValueError("Unknown report section")
