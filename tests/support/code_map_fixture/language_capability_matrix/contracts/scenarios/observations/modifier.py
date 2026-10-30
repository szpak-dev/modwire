from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.authored_modifier import AuthoredModifier
from ....values.names.qualified_name import QualifiedName


class ModifierObservation(FixtureModel):
    kind: Literal["modifier"]
    owner: QualifiedName
    modifier: AuthoredModifier
