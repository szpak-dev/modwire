from ...values.models.value_model import ValueModel
from .identity import FileId
from .types import SourceCallResolution


class SourceCall(ValueModel):
    source_callable_id: str
    target_callable_id: str = ""
    source_id: FileId
    line: int
    expression: str
    resolution: SourceCallResolution
    target_name: str
