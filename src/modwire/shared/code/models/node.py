from pydantic import ConfigDict

from modwire.shared.code.models.identity import FileId
from modwire.shared.values.models.value_model import ValueModel


class Node(ValueModel):
    model_config = ConfigDict(frozen=True)
    id: FileId
    kind: str = "file"
