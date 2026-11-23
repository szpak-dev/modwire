from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .kind import SourceTypeKind


class SourceTypeUnsupported(ImmutableCodeValue):
    kind: Literal[SourceTypeKind.UNSUPPORTED] = SourceTypeKind.UNSUPPORTED
