from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_symbol_kind import SourceSymbolKind
from ....shared.code.models.source_visibility import SourceVisibility
from ....shared.values.models.value_model import ValueModel


class ManifestSymbol(ValueModel):
    id: DeclarationIdentity
    qualified_name: str
    kind: SourceSymbolKind
    visibility: SourceVisibility
