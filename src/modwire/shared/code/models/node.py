from pydantic import ConfigDict

from ...values.models.value_model import ValueModel
from .identity import FileId


class Node(ValueModel):
    model_config = ConfigDict(frozen=True)
    id: FileId
    kind: str = "file"
