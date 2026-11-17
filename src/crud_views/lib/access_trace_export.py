"""Internal wire models for the cv_access version-1 trace. Importable before Django configuration.

This is not a public Python API: ``AccessTrace``/``AccessStep`` and ``to_dict()`` remain the Python interface,
while the JSON document and the schema generated here are the machine contract.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Outcome = Literal["allowed", "denied", "not_found", "login_redirect", "no_such_route", "error"]
Kind = Literal[
    "route",
    "validation",
    "actor_admission",
    "ancestor_lookup",
    "ancestor_gate",
    "own_permission",
    "object_lookup",
    "object_grant",
    "list_filter",
    "action_state",
    "manage_gate",
    "custom_gate",
    "login_middleware",
    "limitation",
]
StepResult = Literal[
    "passed", "denied", "not_found", "login_redirect", "error", "skipped", "not_reached", "not_evaluated", "unavailable"
]
Provider = Literal["core", "guardian", "model", "none"]


class _TraceModel(BaseModel):
    # Unknown keys are rejected here; the documentation still asks consumers to tolerate additive fields.
    # allow_inf_nan is inert (no float fields) and kept only so the options shared with manage_report.WireModel
    # stay identical.
    model_config = ConfigDict(strict=True, allow_inf_nan=False, revalidate_instances="always", extra="forbid")


class TraceUser(_TraceModel):  # empty before actor resolution, otherwise all four keys with boolean flags
    pk: str | None = None
    username: str | None = None
    active: bool | None = None
    anonymous: bool | None = None

    @model_validator(mode="after")
    def _empty_or_complete(self):
        # The fields stay optional so that `{}` validates; this rejects partial actors and null flags.
        if self.model_fields_set and (
            self.model_fields_set != set(type(self).model_fields) or self.active is None or self.anonymous is None
        ):
            raise ValueError("user must be empty or carry pk, username, active and anonymous")
        return self


class ObjectIdentity(_TraceModel):
    model: str
    pk: str | None


class TraceException(_TraceModel):
    class_: str = Field(alias="class")
    message: str


class Counts(_TraceModel):
    visible: int
    total: int | None


class PlanRow(_TraceModel):  # keys other than kind and viewset may be absent; plan rows have no step number
    kind: Kind
    viewset: str | None
    object: ObjectIdentity | None = None
    key: str | None = None
    group: str | None = None
    permission: str | None = None
    provider: Provider | None = None
    source: str | None = None
    result: Literal["unavailable"] | None = None
    exception: TraceException | None = None


class Step(_TraceModel):  # every AccessStep key is always present
    n: int
    kind: Kind
    viewset: str | None
    object: ObjectIdentity | None
    key: str | None
    permission: str | None
    group: str | None
    provider: Provider | None
    source: str | None
    result: StepResult | None
    how: str | None
    message: str | None
    exception: TraceException | None
    counts: Counts | None


class AccessTraceExport(_TraceModel):
    path: str
    route: str | None
    view: str | None
    user: TraceUser
    outcome: Outcome
    decided_by: int | None
    plan: list[PlanRow]
    steps: list[Step]
    untraced: list[str]
    version: Literal[1]

    @field_validator("version", mode="before")
    @classmethod
    def _version_must_be_int(cls, value):
        # Strict Literal[1] accepts True and 1.0 at Pydantic 2.14, and the document would then say `true` or `1.0`.
        if type(value) is not int:
            raise ValueError("version must be the integer 1")
        return value


def validate_export(data):
    return AccessTraceExport.model_validate(data)


def export_schema():
    # Validation mode: Pydantic 2.2.1 marks defaulted fields as required in serialization mode (D-11).
    return AccessTraceExport.model_json_schema(mode="validation")
