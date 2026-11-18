from typing import Annotated, Literal

from ....values.models.value_reference import ValueReference
from ..immutable_code_value import ImmutableCodeValue
from .declaration_identity import DeclarationIdentity
from .source_scope_kind import SourceScopeKind


class SourceDeclarationScope(ImmutableCodeValue):
    kind: Literal[SourceScopeKind.DECLARATION] = SourceScopeKind.DECLARATION
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
