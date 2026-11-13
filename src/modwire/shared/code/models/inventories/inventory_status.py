from enum import StrEnum


class InventoryStatus(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNSUPPORTED = "unsupported"
    UNOBSERVED = "unobserved"
    NOT_APPLICABLE = "not_applicable"
