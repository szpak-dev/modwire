from ....values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_namespace_kind import SourceNamespaceKind
from .source_placement import SourcePlacement


class SourceNamespace(ValueModel):
    kind: SourceNamespaceKind
    declaration_id: DeclarationIdentity
    placement: SourcePlacement

    @property
    def qualified_name(self) -> str:
        return self.declaration_id.qualified_name
