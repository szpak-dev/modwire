from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestParameter(ValueModel):
    id: str
    callable_id: DeclarationIdentity
    position: int
    name: str
    kind: str
    has_default: bool
