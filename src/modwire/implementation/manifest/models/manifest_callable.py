from ....shared.code.models.callables.source_callable_kind import SourceCallableKind
from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel


class ManifestCallable(ValueModel):
    symbol_id: DeclarationIdentity
    callable_kind: SourceCallableKind
