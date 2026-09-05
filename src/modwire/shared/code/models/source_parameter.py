from modwire.shared.code.models.types import SourceParameterKind
from modwire.shared.values.models.value_model import ValueModel


class SourceParameter(ValueModel):
    name: str
    annotation: str = ""
    kind: SourceParameterKind
    has_default: bool = False
