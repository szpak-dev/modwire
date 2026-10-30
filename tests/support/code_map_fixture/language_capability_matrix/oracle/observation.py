from dataclasses import dataclass

from modwire.application import SourceFile, SourceParameter

from .dependencies import FixtureDependencyObservation
from .missing import MissingFactObservation


@dataclass(frozen=True)
class PublicFactObservation:
    value: SourceFile | tuple[SourceParameter, ...] | FixtureDependencyObservation | MissingFactObservation
