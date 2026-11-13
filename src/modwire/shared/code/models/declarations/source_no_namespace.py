from typing import Literal

from ....values.models.value_model import ValueModel
from .source_namespace_membership_kind import SourceNamespaceMembershipKind


class SourceNoNamespace(ValueModel):
    kind: Literal[SourceNamespaceMembershipKind.NONE] = SourceNamespaceMembershipKind.NONE
