from ....values.models.value_model import ValueModel
from ..dependencies.node import Node
from ..sources.identity import FileId
from ..sources.source_file import SourceFile


class DependencyNodeResult(ValueModel):
    node_id: FileId
    node: Node
    file: SourceFile | None
