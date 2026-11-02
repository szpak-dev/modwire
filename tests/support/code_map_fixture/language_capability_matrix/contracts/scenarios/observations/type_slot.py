from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.type_slot_role import TypeSlotRole
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.position import SourcePosition


class TypeSlotObservation(FixtureModel):
    kind: Literal["type_slot"]
    owner: QualifiedName
    role: TypeSlotRole
    position: SourcePosition
