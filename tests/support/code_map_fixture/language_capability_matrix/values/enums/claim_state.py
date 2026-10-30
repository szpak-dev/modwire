from enum import StrEnum


class ClaimState(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    UNSUPPORTED = "unsupported"
