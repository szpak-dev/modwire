from typing import Literal

from modwire.application import SourceParameterKind

from .....fixture_model import FixtureModel


class ParameterKindObservation(FixtureModel):
    kind: Literal["parameter_kinds"]
    present: tuple[SourceParameterKind, ...]
