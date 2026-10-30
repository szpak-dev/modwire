from typing import Literal

from modwire.application import SourceMemberKind

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier
from ....values.names.qualified_name import QualifiedName


class AttributeObservation(FixtureModel):
    kind: Literal["attribute"]
    owner: QualifiedName
    name: Identifier
    member_kind: SourceMemberKind
