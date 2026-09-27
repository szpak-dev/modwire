from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestCallable(ValueModel):
    symbol_id: DeclarationIdentity
    callable_kind: str
