from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.line import SourceLine


class ExactSpanObservation(FixtureModel):
    kind: Literal["exact_span"]
    owner: QualifiedName
    start: SourceLine
    end: SourceLine
