from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .identity import FileId
from .source_call_resolution import SourceCallResolution


class SourceCall(ValueModel):
    source_callable_id: DeclarationIdentity
    target_callable_id: DeclarationIdentity | None
    source_id: FileId
    line: int
    expression: str
    resolution: SourceCallResolution
    target_name: str
