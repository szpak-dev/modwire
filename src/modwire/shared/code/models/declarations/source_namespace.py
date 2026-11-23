from typing import Annotated

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from .declaration_identity import DeclarationIdentity
from .source_namespace_kind import SourceNamespaceKind
from .source_placement import SourcePlacement


class SourceNamespace(ValueModel):
    kind: SourceNamespaceKind
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    placement: Annotated[SourcePlacement, ValueReference()]

    @property
    def qualified_name(self) -> str:
        return self.declaration_id.qualified_name
