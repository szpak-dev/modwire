import ast
from pathlib import Path


class TupleCardinalityVisitor(ast.NodeVisitor):
    def __init__(self, source_root: Path, path: Path) -> None:
        self.source_root = source_root
        self.path = path
        self.ambiguous: list[str] = []

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if ast.unparse(node.value) == "tuple" and "," not in ast.unparse(node.slice):
            self.ambiguous.append(f"{self.path.relative_to(self.source_root)}:{node.lineno}")
        self.generic_visit(node)
