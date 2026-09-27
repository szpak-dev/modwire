from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestInheritance(ValueModel):
    source_symbol_id: DeclarationIdentity
    kind: str
    target_reference: str
