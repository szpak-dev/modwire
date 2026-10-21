from typing import Literal, TypedDict


class SourceParseFailurePayload(TypedDict):
    code: Literal["source_parse"]
    language: str
    path: str
    line: int
    column: int
    diagnostic: str
