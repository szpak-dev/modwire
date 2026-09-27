from ...values.models.value_model import ValueModel
from .source_member_kind import SourceMemberKind
from .types import SourceVisibility


class SourceClassProperty(ValueModel):
    name: str
    is_optional: bool
    annotation: str
    visibility: SourceVisibility
    member_kind: SourceMemberKind
