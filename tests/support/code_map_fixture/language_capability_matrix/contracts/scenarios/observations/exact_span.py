from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.line import SourceLine


class ExactSpanObservation(FixtureModel):
    kind: Literal[ObservationKind.EXACT_SPAN]
    owner: QualifiedName
    start: SourceLine
    end: SourceLine
