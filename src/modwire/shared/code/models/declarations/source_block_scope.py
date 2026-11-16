from typing import Literal

from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from .source_declaration_scope import SourceDeclarationScope
from .source_file_scope import SourceFileScope
from .source_scope_kind import SourceScopeKind


class SourceBlockScope(ImmutableCodeValue):
    kind: Literal[SourceScopeKind.BLOCK] = SourceScopeKind.BLOCK
    container: SourceFileScope | SourceDeclarationScope = Field(discriminator="kind")
    start_utf8_offset: int = Field(ge=0)
    end_utf8_offset: int = Field(ge=0)
