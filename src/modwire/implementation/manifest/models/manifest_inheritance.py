from typing import Self

from pydantic import model_validator

from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_relation_kind import SourceRelationKind
from ....shared.values.models.value_model import ValueModel


class ManifestInheritance(ValueModel):
    source_symbol_id: DeclarationIdentity
    kind: SourceRelationKind
    target_reference: str

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is SourceRelationKind.IMPORTS:
            raise ValueError("Manifest inheritance must use extends or implements.")
        return self
