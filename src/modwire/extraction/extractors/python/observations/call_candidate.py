import ast
from dataclasses import dataclass

from .....shared.code.models.declaration_identity import DeclarationIdentity
from .....shared.code.models.identity import FileId
from .call_reference import PythonCallReference


@dataclass(frozen=True)
class PythonCallCandidate:
    node: ast.Call
    reference: PythonCallReference
    ordinal: int
    source_qualified_name: str
    owner_name: str
    source_id: FileId
    source_callable_id: DeclarationIdentity
    by_name: dict[str, list[DeclarationIdentity]]
    by_qualified_name: dict[str, list[DeclarationIdentity]]
    constructors_by_name: dict[str, list[DeclarationIdentity]]
