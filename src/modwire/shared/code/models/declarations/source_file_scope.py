from typing import Literal

from ....values.models.value_model import ValueModel
from .source_scope_kind import SourceScopeKind


class SourceFileScope(ValueModel):
    kind: Literal[SourceScopeKind.FILE] = SourceScopeKind.FILE
