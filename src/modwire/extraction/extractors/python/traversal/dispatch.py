import ast
from collections.abc import Callable
from dataclasses import dataclass

from .....shared.code.models.inventories.inventory_limitation import InventoryLimitation
from ..observations.value_candidate import PythonValueCandidate
from .context import PythonTraversalContext


@dataclass(frozen=True)
class PythonObservationDispatch:
    visit: Callable[[ast.AST, int, PythonTraversalContext], None]
    observe_property_method: Callable[[ast.AST, ast.FunctionDef | ast.AsyncFunctionDef, tuple[int, int], int], None]
    observe_call: Callable[[ast.AST, ast.Call], None]
    bind_lambda: Callable[[ast.expr, ast.expr], None]
    bind_lambda_name: Callable[[ast.expr, ast.Lambda], None]
    observe_assignment: Callable[[ast.expr, ast.Assign | ast.AnnAssign, PythonTraversalContext], None]
    observe_class_property: Callable[[ast.AST, ast.Assign | ast.AnnAssign, PythonValueCandidate], None]
    observe_unresolved_binding: Callable[[ast.expr_context, str, PythonTraversalContext], None]
    observe_export_mutation: Callable[[ast.AST, ast.stmt | ast.expr, PythonTraversalContext], None]
    limit_exports: Callable[[ast.AST, ast.stmt | ast.expr], None]
    limit_property_scope: Callable[[ast.AST, InventoryLimitation], None]
