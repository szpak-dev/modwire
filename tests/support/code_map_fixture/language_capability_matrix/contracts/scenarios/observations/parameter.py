from typing import Literal

from modwire.application import SourceParameterKind

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.position import SourcePosition


class ParameterObservation(FixtureModel):
    kind: Literal["parameter"]
    owner: QualifiedName
    name: Identifier
    position: SourcePosition
    parameter_kind: SourceParameterKind
    has_default: bool
