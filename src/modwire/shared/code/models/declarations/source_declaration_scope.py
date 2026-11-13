from typing import Literal

from ....values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_scope_kind import SourceScopeKind


class SourceDeclarationScope(ValueModel):
    kind: Literal[SourceScopeKind.DECLARATION] = SourceScopeKind.DECLARATION
    declaration_id: DeclarationIdentity
