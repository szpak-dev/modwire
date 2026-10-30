from typing import Literal

from modwire.application import SourceCallResolution

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class CallObservation(FixtureModel):
    kind: Literal["call"]
    owner: QualifiedName
    target: QualifiedName
    resolution: SourceCallResolution
