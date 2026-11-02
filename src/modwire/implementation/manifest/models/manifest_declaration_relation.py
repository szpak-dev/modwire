from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.code.models.declarations.source_declaration_relation_kind import SourceDeclarationRelationKind
from ....shared.values.models.value_model import ValueModel


class ManifestDeclarationRelation(ValueModel):
    source_symbol_id: DeclarationIdentity
    kind: SourceDeclarationRelationKind
    target_reference: str
