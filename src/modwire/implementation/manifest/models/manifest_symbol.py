from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_visibility import SourceVisibility
from ....shared.values.models.value_model import ValueModel
from .manifest_symbol_kind import ManifestSymbolKind


class ManifestSymbol(ValueModel):
    id: DeclarationIdentity
    qualified_name: str
    kind: ManifestSymbolKind
    visibility: SourceVisibility
