from enum import StrEnum


class FixtureRole(StrEnum):
    EXTENSIONS = "extensions"
    GAPS = "gaps"
    TYPES = "types"
    PARAMETERS = "parameters"
    STRUCTURAL = "structural"
