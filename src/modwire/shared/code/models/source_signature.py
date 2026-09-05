from modwire.shared.code.models.types import SourceSignatureKind
from modwire.shared.values.models.value_model import ValueModel


class SourceSignature(ValueModel):
    kind: SourceSignatureKind
    line_count: int
    declared_args: int
    optional_args: int
