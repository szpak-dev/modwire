from typing import Literal

from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from .source_namespace_membership_kind import SourceNamespaceMembershipKind
from .source_resolved_target import SourceResolvedTarget
from .source_unresolved_target import SourceUnresolvedTarget


class SourceNamespaceMembership(ImmutableCodeValue):
    kind: Literal[SourceNamespaceMembershipKind.MEMBER] = SourceNamespaceMembershipKind.MEMBER
    namespace_reference: str = Field(min_length=1)
    target: SourceResolvedTarget | SourceUnresolvedTarget = Field(discriminator="kind")
