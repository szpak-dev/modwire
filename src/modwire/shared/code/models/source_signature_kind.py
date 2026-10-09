from enum import StrEnum


class SourceSignatureKind(StrEnum):
    CALL = "call"
    CONSTRUCT = "construct"
    INDEX = "index"
