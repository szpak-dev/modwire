from ...values.models.value_model import ValueModel
from .source_signature_kind import SourceSignatureKind


class SourceSignature(ValueModel):
    kind: SourceSignatureKind
    line_count: int
    declared_args: int
    optional_args: int
