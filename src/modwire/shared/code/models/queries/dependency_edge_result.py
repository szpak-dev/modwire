from ....values.models.value_model import ValueModel
from ..dependencies.edge import Edge
from ..sources.source_file import SourceFile


class DependencyEdgeResult(ValueModel):
    edge: Edge
    source_file: SourceFile | None
    target_file: SourceFile | None
