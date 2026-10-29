from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_declaration_relation_kind import SourceDeclarationRelationKind
from ....shared.values.models.value_model import ValueModel


class ManifestDeclarationRelation(ValueModel):
    source_symbol_id: DeclarationIdentity
    kind: SourceDeclarationRelationKind
    target_reference: str
