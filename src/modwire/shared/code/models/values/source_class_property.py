from typing import Self

from pydantic import Field, model_validator

from ....values.models.value_model import ValueModel
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_member_kind import SourceMemberKind
from ..declarations.source_visibility import SourceVisibility
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from .source_assigned_value import SourceAssignedValue


class SourceClassProperty(ValueModel):
    declaration_id: DeclarationIdentity
    owner_declaration_id: DeclarationIdentity
    name: str
    is_optional: bool
    type: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported
    visibility: SourceVisibility
    member_kind: SourceMemberKind
    assigned_values: tuple[SourceAssignedValue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.declaration_id.family is not DeclarationFamily.PROPERTY:
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_FAMILY, self.name)
        if self.declaration_id.source_id != self.owner_declaration_id.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_MEMBER_OWNER, self.name)
        return self
