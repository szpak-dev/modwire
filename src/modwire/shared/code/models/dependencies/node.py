from ....values.models.value_model import ValueModel
from ..sources.identity import FileId
from .node_kind import NodeKind


class Node(ValueModel):
    id: FileId
    kind: NodeKind = NodeKind.FILE
