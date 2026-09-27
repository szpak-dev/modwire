from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_relation_kind import SourceRelationKind


class SourceInheritance(ValueModel):
    source_declaration_id: DeclarationIdentity
    kind: SourceRelationKind
    target_reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is SourceRelationKind.IMPORTS:
            raise ValueError("Source inheritance must use extends or implements.")
        return self
