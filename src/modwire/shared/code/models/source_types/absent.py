from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .kind import SourceTypeKind


class SourceTypeAbsent(ImmutableCodeValue):
    kind: Literal[SourceTypeKind.ABSENT] = SourceTypeKind.ABSENT
