from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestSymbol(ValueModel):
    id: DeclarationIdentity
    qualified_name: str
    kind: str
    visibility: str
