from ....shared.code.models.callables.source_parameter_kind import SourceParameterKind
from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestParameter(ValueModel):
    id: str
    callable_id: DeclarationIdentity
    position: int
    name: str
    kind: SourceParameterKind
    has_default: bool
