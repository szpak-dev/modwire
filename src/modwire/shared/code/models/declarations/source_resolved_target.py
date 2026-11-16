from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .declaration_identity import DeclarationIdentity
from .source_binding_kind import SourceBindingKind


class SourceResolvedTarget(ImmutableCodeValue):
    kind: Literal[SourceBindingKind.RESOLVED] = SourceBindingKind.RESOLVED
    declaration_id: DeclarationIdentity
