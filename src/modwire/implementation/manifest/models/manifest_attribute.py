from typing import Self

from pydantic import Field, model_validator

from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_assigned_value import SourceAssignedValue
from ....shared.code.models.source_member_kind import SourceMemberKind
from ....shared.code.models.types import SourceVisibility
from ....shared.values.models.value_model import ValueModel


class ManifestAttribute(ValueModel):
    id: str
    owner_symbol_id: DeclarationIdentity
    name: str
    is_optional: bool
    annotation: str
    visibility: SourceVisibility
    member_kind: SourceMemberKind
    assigned_values: tuple[SourceAssignedValue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"{self.owner_symbol_id.canonical()}::attribute:{self.name}":
            raise ValueError("Manifest attribute identity must match its owner and name.")
        return self
