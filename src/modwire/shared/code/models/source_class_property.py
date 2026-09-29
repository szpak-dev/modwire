from pydantic import Field

from ...values.models.value_model import ValueModel
from .source_assigned_value import SourceAssignedValue
from .source_member_kind import SourceMemberKind
from .types import SourceVisibility


class SourceClassProperty(ValueModel):
    name: str
    is_optional: bool
    annotation: str
    visibility: SourceVisibility
    member_kind: SourceMemberKind
    assigned_values: tuple[SourceAssignedValue, ...] = Field(min_length=1)
