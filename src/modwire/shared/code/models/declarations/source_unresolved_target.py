from typing import Literal

from ....values.models.value_model import ValueModel
from .source_binding_kind import SourceBindingKind
from .source_unresolved_reason import SourceUnresolvedReason


class SourceUnresolvedTarget(ValueModel):
    kind: Literal[SourceBindingKind.UNRESOLVED] = SourceBindingKind.UNRESOLVED
    reason: SourceUnresolvedReason
