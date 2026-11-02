import ast
from pathlib import Path

from .tuple_cardinality_visitor import TupleCardinalityVisitor


class TestPythonTupleCardinality:
    def test_every_tuple_annotation_declares_fixed_or_variadic_cardinality(self) -> None:
        source_root = Path(__file__).parents[3] / "src" / "modwire"
        ambiguous: list[str] = []

        for path in sorted(source_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            visitor = TupleCardinalityVisitor(source_root, path)
            visitor.visit(tree)
            ambiguous.extend(visitor.ambiguous)

        assert ambiguous == []
