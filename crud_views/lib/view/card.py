from pydantic import BaseModel, model_validator


class CardAction(BaseModel):
    key: str = ""
    label: str | None = None
    no_label: bool = False
    variant: str = "secondary"
    flex: bool = False
    child_name: str | None = None
    child_key: str = "list"

    @model_validator(mode="after")
    def check_key_or_child(self):
        if not self.key and not self.child_name:
            raise ValueError("CardAction requires either 'key' or 'child_name'")
        return self
