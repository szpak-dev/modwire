from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.position import SourcePosition


class ParameterObservation(FixtureModel):
    kind: Literal["parameter"]
    owner: QualifiedName
    position: SourcePosition
