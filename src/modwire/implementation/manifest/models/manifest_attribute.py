from typing import Self

from pydantic import Field, model_validator

from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.code.models.declarations.source_visibility import SourceVisibility
from ....shared.code.models.values.source_assigned_value import SourceAssignedValue
from ....shared.code.models.values.source_member_kind import SourceMemberKind
from ....shared.values.models.value_model import ValueModel
from .implementation_manifest_validation_error import ImplementationManifestValidationError
from .implementation_manifest_violation import ImplementationManifestViolation


class ManifestAttribute(ValueModel):
    id: str
    owner_symbol_id: DeclarationIdentity
    name: str
    is_optional: bool
    visibility: SourceVisibility
    member_kind: SourceMemberKind
    assigned_values: tuple[SourceAssignedValue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"{self.owner_symbol_id.canonical()}::attribute:{self.name}":
            raise ImplementationManifestValidationError(
                ImplementationManifestViolation.INCONSISTENT_ATTRIBUTE_IDENTITY, self.id
            )
        return self
