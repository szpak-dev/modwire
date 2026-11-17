from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from .source_parameter_kind import SourceParameterKind


class SourceParameter(ImmutableCodeValue):
    name: str
    type: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported = Field(union_mode="left_to_right")
    kind: SourceParameterKind
    has_default: bool = False
