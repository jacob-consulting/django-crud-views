from pydantic import BaseModel


class CardAction(BaseModel):
    """
    Configuration for a single action button rendered on a card.
    """

    key: str
    label: str | None = None
    no_label: bool = False
    variant: str = "secondary"
    flex: bool = False
