from typing import Literal

from ....values.models.value_model import ValueModel
from .kind import SourceTypeKind


class SourceTypeAbsent(ValueModel):
    kind: Literal[SourceTypeKind.ABSENT] = SourceTypeKind.ABSENT
