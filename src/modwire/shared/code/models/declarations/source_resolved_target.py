from typing import Annotated, Literal

from ....values.models.value_reference import ValueReference
from ..immutable_code_value import ImmutableCodeValue
from .declaration_identity import DeclarationIdentity
from .source_binding_kind import SourceBindingKind


class SourceResolvedTarget(ImmutableCodeValue):
    kind: Literal[SourceBindingKind.RESOLVED] = SourceBindingKind.RESOLVED
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
