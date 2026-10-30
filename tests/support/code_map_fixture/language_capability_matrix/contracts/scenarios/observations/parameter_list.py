from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class ParameterListObservation(FixtureModel):
    kind: Literal["parameter_list"]
    owner: QualifiedName
