from enum import StrEnum


class Conclusion(StrEnum):
    SOURCE_INVENTORY = "C01"
    DECLARATIONS = "C02"
    OWNERSHIP = "C03"
    PROPERTIES = "C04"
    CALLABLES = "C05"
    PARAMETERS = "C06"
    TYPES = "C07"
    TYPE_DECLARATIONS = "C08"
    QUALIFIERS = "C09"
    RELATIONSHIPS = "C10"
    COMPLETENESS = "C11"
    PROVENANCE = "C12"
    CONTRACT = "contract"
