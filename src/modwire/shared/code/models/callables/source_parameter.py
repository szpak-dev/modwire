from ....values.models.value_model import ValueModel
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from .source_parameter_kind import SourceParameterKind


class SourceParameter(ValueModel):
    name: str
    type: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported
    kind: SourceParameterKind
    has_default: bool = False
