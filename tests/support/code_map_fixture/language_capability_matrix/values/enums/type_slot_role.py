from enum import StrEnum


class TypeSlotRole(StrEnum):
    RETURN = "return"
    PARAMETER = "parameter"
    ATTRIBUTE = "attribute"
