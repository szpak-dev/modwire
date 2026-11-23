import ast
from dataclasses import dataclass

from .....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from .....shared.code.models.declarations.source_resolved_target import SourceResolvedTarget
from .....shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from .call_reference import PythonCallReference


@dataclass(frozen=True)
class PythonCallCandidate:
    node: ast.Call
    reference: PythonCallReference
    ordinal: int
    source_callable_id: DeclarationIdentity
    target: SourceResolvedTarget | SourceUnresolvedTarget
