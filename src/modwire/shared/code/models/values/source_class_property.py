from typing import Annotated, Self

from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_placement import SourcePlacement
from ..declarations.source_visibility import SourceVisibility
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from .source_assigned_value import SourceAssignedValue
from .source_member_kind import SourceMemberKind


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourceClassProperty:
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    owner_declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    name: str
    is_optional: bool
    type: Annotated[SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported, ValueReference()] = Field(
        union_mode="left_to_right"
    )
    visibility: SourceVisibility
    member_kind: SourceMemberKind
    placement: Annotated[SourcePlacement, ValueReference()]
    assigned_values: tuple[Annotated[SourceAssignedValue, ValueReference()], ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.declaration_id.family is not DeclarationFamily.PROPERTY:
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_FAMILY, self.name)
        if self.declaration_id.source_id != self.owner_declaration_id.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_MEMBER_OWNER, self.name)
        return self
