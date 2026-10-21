import ast

from .base_test import ApplicationTestCase


class TestFailurePolicy(ApplicationTestCase):
    def test_production_raises_only_domain_failures_or_explicit_contract_sentinels(self) -> None:
        source_root = self.repository / "src/modwire"
        documents = {
            path: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for path in sorted(source_root.rglob("*.py"))
        }
        inheritance = {
            node.name: tuple(self.name(base) for base in node.bases)
            for document in documents.values()
            for node in ast.walk(document)
            if isinstance(node, ast.ClassDef)
        }
        entrypoints = {
            source_root / "__main__.py",
            source_root / "extraction/extractors/resources/java/build.py",
            source_root / "extraction/extractors/resources/php/build.py",
            source_root / "extraction/extractors/resources/python/script.py",
            source_root / "extraction/extractors/resources/typescript/build.py",
        }
        violations: list[str] = []

        for path, document in documents.items():
            parents = {child: parent for parent in ast.walk(document) for child in ast.iter_child_nodes(parent)}
            for raised in (node for node in ast.walk(document) if isinstance(node, ast.Raise)):
                if raised.exc is None:
                    continue
                name = self.name(raised.exc.func if isinstance(raised.exc, ast.Call) else raised.exc)
                if name == "SystemExit" and path in entrypoints:
                    continue
                if name == "NotImplementedError" and self.in_abstract_method(raised, parents):
                    continue
                if name[:1].islower():
                    continue
                if name in inheritance and self.inherits(name, "ModwireError", inheritance):
                    continue
                violations.append(f"{path.relative_to(self.repository)}:{raised.lineno}:{name}")

        assert violations == []

    def name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return type(node).__name__

    def inherits(self, child: str, parent: str, inheritance: dict[str, tuple[str, ...]]) -> bool:
        pending = list(inheritance.get(child, ()))
        visited: set[str] = set()
        while pending:
            candidate = pending.pop()
            if candidate == parent:
                return True
            if candidate not in visited:
                visited.add(candidate)
                pending.extend(inheritance.get(candidate, ()))
        return False

    def in_abstract_method(self, node: ast.Raise, parents: dict[ast.AST, ast.AST]) -> bool:
        current: ast.AST = node
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return any(self.name(decorator) == "abstractmethod" for decorator in current.decorator_list)
        return False
