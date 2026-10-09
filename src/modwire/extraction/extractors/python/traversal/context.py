import ast
from dataclasses import dataclass

from .traversal_role import PythonTraversalRole


@dataclass(frozen=True)
class PythonTraversalContext:
    module: ast.Module
    parent_role: PythonTraversalRole
    class_name: str
    lambda_root: str
    lambda_owner: str
    lambda_root_ordinal: int
    owners: tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...]
    property_contexts: tuple[tuple[str, int, int, ast.FunctionDef | ast.AsyncFunctionDef], ...]
    direct_classes: tuple[tuple[str, int, int], ...]
    active_lambda: ast.Module | ast.Lambda
