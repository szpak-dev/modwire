import ast
from dataclasses import dataclass

from .....shared.code.models.identity import FileId
from .call_reference import PythonCallReference


@dataclass(frozen=True)
class PythonCallCandidate:
    node: ast.Call
    reference: PythonCallReference
    source_qualified_name: str
    owner_name: str
    source_id: FileId
    source_callable_id: str
    by_name: dict[str, str]
    by_qualified_name: dict[str, str]
    constructors_by_name: dict[str, str]
