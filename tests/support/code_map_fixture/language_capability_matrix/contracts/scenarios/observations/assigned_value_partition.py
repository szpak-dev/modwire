from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier
from ....values.names.qualified_name import QualifiedName


class AssignedValuePartitionObservation(FixtureModel):
    kind: Literal["assigned_value_partition"]
    owner: QualifiedName
    absent: tuple[Identifier, ...]
    literal: tuple[Identifier, ...]
    reference: tuple[Identifier, ...]
    call: tuple[Identifier, ...]
    unresolved: tuple[Identifier, ...]
