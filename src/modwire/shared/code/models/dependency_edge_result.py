from modwire.shared.code.models.edge import Edge
from modwire.shared.code.models.source_file import SourceFile
from modwire.shared.values.models.value_model import ValueModel


class DependencyEdgeResult(ValueModel):
    edge: Edge
    source_file: SourceFile | None
    target_file: SourceFile | None
