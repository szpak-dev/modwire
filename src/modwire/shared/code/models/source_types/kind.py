from enum import StrEnum


class SourceTypeKind(StrEnum):
    REFERENCE = "reference"
    ABSENT = "absent"
    UNSUPPORTED = "unsupported"
