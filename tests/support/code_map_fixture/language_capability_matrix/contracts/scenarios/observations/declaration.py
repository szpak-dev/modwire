from typing import Literal

from modwire.application import SourceSymbolKind

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class DeclarationObservation(FixtureModel):
    kind: Literal["declaration"]
    qualified_name: QualifiedName
    declaration_kind: SourceSymbolKind
