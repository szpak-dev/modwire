from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .declaration_identity import DeclarationIdentity
from .source_scope_kind import SourceScopeKind


class SourceDeclarationScope(ImmutableCodeValue):
    kind: Literal[SourceScopeKind.DECLARATION] = SourceScopeKind.DECLARATION
    declaration_id: DeclarationIdentity
