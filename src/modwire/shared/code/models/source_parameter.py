from ...values.models.value_model import ValueModel
from .types import SourceParameterKind


class SourceParameter(ValueModel):
    name: str
    annotation: str = ""
    kind: SourceParameterKind
    has_default: bool = False
