from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.enums.type_slot_role import TypeSlotRole
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.position import SourcePosition


class TypeReferenceObservation(FixtureModel):
    kind: Literal[ObservationKind.TYPE_REFERENCE]
    owner: QualifiedName
    role: TypeSlotRole
    position: SourcePosition
