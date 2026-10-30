from typing import Literal

from modwire.application import SourceNamespaceKind

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class NamespaceObservation(FixtureModel):
    kind: Literal["namespace"]
    qualified_name: QualifiedName
    namespace_kind: SourceNamespaceKind
