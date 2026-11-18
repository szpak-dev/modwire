from typing import Annotated

from pydantic import Field

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from .declaration_identity import DeclarationIdentity
from .source_declaration_relation_kind import SourceDeclarationRelationKind
from .source_resolved_target import SourceResolvedTarget
from .source_unresolved_target import SourceUnresolvedTarget


class SourceDeclarationRelation(ValueModel):
    source_declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    kind: SourceDeclarationRelationKind
    target_reference: str = Field(min_length=1)
    target: Annotated[
        Annotated[SourceResolvedTarget | SourceUnresolvedTarget, Field(discriminator="kind")], ValueReference()
    ]
