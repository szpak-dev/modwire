from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class SpanOwnerObservation(FixtureModel):
    kind: Literal["span_owner"]
    owner: QualifiedName
