from typing import Literal

from modwire.application import SourceCallableKind

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class ManifestCallableObservation(FixtureModel):
    kind: Literal["callable"]
    qualified_name: QualifiedName
    callable_kind: SourceCallableKind
