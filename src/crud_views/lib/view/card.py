from pydantic import BaseModel, model_validator

from crud_views.lib.lazy import LazyStr

from .label_mode import LABEL_MODES, is_label_mode


class CardAction(BaseModel):
    key: str = ""
    label: LazyStr | None = None
    no_label: bool = False  # superseded by label_mode="icon"; kept working, and an error alongside label_mode
    # None: the view's cv_get_card_actions_label_mode(), its attribute or else the defaults map; one of LABEL_MODES
    label_mode: str | None = None
    variant: str | None = None  # None: the target view's cv_action_variant
    flex: bool = False
    child_name: str | None = None
    child_key: str = "list"

    @model_validator(mode="after")
    def check_key_or_child(self):
        if not self.key and not self.child_name:
            raise ValueError("CardAction requires either 'key' or 'child_name'")
        return self

    @model_validator(mode="after")
    def check_label_mode(self):
        if self.label_mode is None:
            return self
        if not is_label_mode(self.label_mode):
            raise ValueError(f"label_mode must be one of {sorted(LABEL_MODES)}, got {self.label_mode!r}")
        if self.no_label:
            raise ValueError("no_label and label_mode cannot be combined; use label_mode alone")
        return self
