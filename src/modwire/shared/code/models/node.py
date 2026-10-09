from pydantic import ConfigDict

from ...values.models.value_model import ValueModel
from .identity import FileId
from .node_kind import NodeKind


class Node(ValueModel):
    model_config = ConfigDict(frozen=True)
    id: FileId
    kind: NodeKind = NodeKind.FILE
