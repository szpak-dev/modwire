from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestAttribute(ValueModel):
    owner_symbol_id: DeclarationIdentity
    name: str
    is_optional: bool
