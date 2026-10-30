from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class AssignedValuesObservation(FixtureModel):
    kind: Literal["assigned_values"]
    owner: QualifiedName
