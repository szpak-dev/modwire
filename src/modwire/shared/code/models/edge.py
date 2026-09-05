from pydantic import ConfigDict

from modwire.shared.code.models.edge_resolution import EdgeResolution
from modwire.shared.code.models.identity import FileId, ImportSpecifier
from modwire.shared.values.models.value_model import ValueModel


class Edge(ValueModel):
    model_config = ConfigDict(frozen=True)
    from_id: FileId
    to_id: FileId | None
    specifier: ImportSpecifier
    resolution: EdgeResolution
    kind: str = "import"
