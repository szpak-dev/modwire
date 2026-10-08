import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ...observations.class_candidate import PythonClassCandidate
from .classifier import PythonClassRule


@injectable(as_type=PythonClassRule, qualifier="10-abstract")
@dataclass(frozen=True)
class AbstractClassRule(PythonClassRule):
    @property
    def order(self) -> int:
        return 10

    def applies(self, candidate: PythonClassCandidate) -> bool:
        node = candidate.node
        return any(ast.unparse(base) in {"ABC", "abc.ABC"} for base in node.bases) or any(
            self.is_abstract_method(statement) for statement in node.body
        )

    def classify(self, candidate: PythonClassCandidate) -> DeclarationFamily:
        return DeclarationFamily.ABSTRACT_CLASS

    @singledispatchmethod
    def is_abstract_method(self, statement: ast.stmt) -> bool:
        return False

    @is_abstract_method.register
    def function_is_abstract(self, statement: ast.FunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "abstractmethod" for item in statement.decorator_list)

    @is_abstract_method.register
    def async_function_is_abstract(self, statement: ast.AsyncFunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "abstractmethod" for item in statement.decorator_list)
