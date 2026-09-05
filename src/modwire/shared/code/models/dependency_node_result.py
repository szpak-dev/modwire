from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.node import Node
from modwire.shared.code.models.source_file import SourceFile
from modwire.shared.values.models.value_model import ValueModel


class DependencyNodeResult(ValueModel):
    node_id: FileId
    node: Node
    file: SourceFile | None
