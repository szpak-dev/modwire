from typing import Literal

from ....shared.values.models.value_model import ValueModel


class ManifestDependency(ValueModel):
    source_id: str
    target_kind: Literal["source", "external", "unresolved"]
    target: str
    specifier: str
    resolution: Literal["resolved", "external", "unresolved"]
    kind: str
