from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from .declaration_identity import DeclarationIdentity
from .source_declaration_relation_kind import SourceDeclarationRelationKind
from .source_resolved_target import SourceResolvedTarget
from .source_unresolved_target import SourceUnresolvedTarget


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourceDeclarationRelation:
    source_declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    kind: SourceDeclarationRelationKind
    target_reference: str = Field(min_length=1)
    target: Annotated[
        Annotated[SourceResolvedTarget | SourceUnresolvedTarget, Field(discriminator="kind")], ValueReference()
    ]
