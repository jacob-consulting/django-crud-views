from enum import IntEnum, StrEnum


class WorkflowComment(IntEnum):
    NONE = 0
    OPTIONAL = 1
    REQUIRED = 2


class BadgeEnum(StrEnum):
    """
    Bootstrap contextual colours for state badges.
    """

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"
