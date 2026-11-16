from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .source_namespace_membership_kind import SourceNamespaceMembershipKind


class SourceNoNamespace(ImmutableCodeValue):
    kind: Literal[SourceNamespaceMembershipKind.NONE] = SourceNamespaceMembershipKind.NONE
