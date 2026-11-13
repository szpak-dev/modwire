from typing import Literal

from ....values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_binding_kind import SourceBindingKind


class SourceResolvedTarget(ValueModel):
    kind: Literal[SourceBindingKind.RESOLVED] = SourceBindingKind.RESOLVED
    declaration_id: DeclarationIdentity
