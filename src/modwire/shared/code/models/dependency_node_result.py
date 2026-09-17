from ...values.models.value_model import ValueModel
from .identity import FileId
from .node import Node
from .source_file import SourceFile


class DependencyNodeResult(ValueModel):
    node_id: FileId
    node: Node
    file: SourceFile | None
