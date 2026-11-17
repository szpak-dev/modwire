from typing import Annotated, Literal

from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from .absent import SourceTypeAbsent
from .kind import SourceTypeKind
from .unsupported import SourceTypeUnsupported


class SourceTypeReference(ImmutableCodeValue):
    kind: Literal[SourceTypeKind.REFERENCE] = SourceTypeKind.REFERENCE
    name: str = Field(min_length=1)
    arguments: tuple[
        Annotated["SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported", Field(union_mode="left_to_right")],
        ...,
    ] = ()
