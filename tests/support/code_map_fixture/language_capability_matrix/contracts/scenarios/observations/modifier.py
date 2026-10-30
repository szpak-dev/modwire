from typing import Literal

from modwire.application import SourceVisibility

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class ModifierObservation(FixtureModel):
    kind: Literal["modifier"]
    owner: QualifiedName
    visibility: SourceVisibility
