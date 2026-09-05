from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.types import SourceCallResolution
from modwire.shared.values.models.value_model import ValueModel


class SourceCall(ValueModel):
    source_callable_id: str
    target_callable_id: str = ""
    source_id: FileId
    line: int
    expression: str
    resolution: SourceCallResolution
    target_name: str
