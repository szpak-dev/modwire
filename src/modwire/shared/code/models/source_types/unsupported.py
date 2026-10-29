from typing import Literal

from ....values.models.value_model import ValueModel
from .kind import SourceTypeKind


class SourceTypeUnsupported(ValueModel):
    kind: Literal[SourceTypeKind.UNSUPPORTED] = SourceTypeKind.UNSUPPORTED
