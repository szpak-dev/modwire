from pydantic import ConfigDict

from ...values.models.value_model import ValueModel
from .edge_resolution import EdgeResolution
from .identity import FileId, ImportSpecifier


class Edge(ValueModel):
    model_config = ConfigDict(frozen=True)
    from_id: FileId
    to_id: FileId | None
    specifier: ImportSpecifier
    resolution: EdgeResolution
    kind: str = "import"
