from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .source_binding_kind import SourceBindingKind
from .source_unresolved_reason import SourceUnresolvedReason


class SourceUnresolvedTarget(ImmutableCodeValue):
    kind: Literal[SourceBindingKind.UNRESOLVED] = SourceBindingKind.UNRESOLVED
    reason: SourceUnresolvedReason
