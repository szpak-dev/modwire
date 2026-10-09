from ...values.models.value_model import ValueModel
from .source_parameter_kind import SourceParameterKind


class SourceParameter(ValueModel):
    name: str
    annotation: str = ""
    kind: SourceParameterKind
    has_default: bool = False
