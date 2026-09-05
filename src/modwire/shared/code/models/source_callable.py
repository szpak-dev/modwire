from pydantic import Field

from .identity import FileId
from .source_callable_symbol import SourceCallableSymbol
from .source_parameter import SourceParameter
from .types import SourceCallableKind


class SourceCallable(SourceCallableSymbol):
    id: str
    source_id: FileId
    qualified_name: str
    owner_name: str = ""
    kind: SourceCallableKind
    line_start: int
    line_end: int
    parameters: list[SourceParameter] = Field(default_factory=list[SourceParameter])
    declared_args: int = 0
    optional_args: int = 0
    return_annotation: str = ""
    decorators: list[str] = Field(default_factory=list[str])
    docstring: str = ""
