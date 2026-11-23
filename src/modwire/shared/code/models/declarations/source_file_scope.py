from typing import Literal

from ..immutable_code_value import ImmutableCodeValue
from .source_scope_kind import SourceScopeKind


class SourceFileScope(ImmutableCodeValue):
    kind: Literal[SourceScopeKind.FILE] = SourceScopeKind.FILE
