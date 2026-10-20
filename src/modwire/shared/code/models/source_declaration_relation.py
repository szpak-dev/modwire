from pydantic import Field

from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_declaration_relation_kind import SourceDeclarationRelationKind


class SourceDeclarationRelation(ValueModel):
    source_declaration_id: DeclarationIdentity
    kind: SourceDeclarationRelationKind
    target_reference: str = Field(min_length=1)
