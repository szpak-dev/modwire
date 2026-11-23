from typing import Annotated

from pydantic import Field

from ....values.models.value_reference import ValueReference
from ..immutable_code_value import ImmutableCodeValue
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from .source_parameter_kind import SourceParameterKind


class SourceParameter(ImmutableCodeValue):
    name: str
    type: Annotated[SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported, ValueReference()] = Field(
        union_mode="left_to_right"
    )
    kind: SourceParameterKind
    has_default: bool = False
