from typing import Literal

from ....values.models.value_model import ValueModel
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_binding_kind import SourceBindingKind


class SourceResolvedExportBinding(ValueModel):
    kind: Literal[SourceBindingKind.RESOLVED] = SourceBindingKind.RESOLVED
    declaration_ids: tuple[DeclarationIdentity, ...]
