import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_parameter import SourceParameter
from ...observations.callable_candidate import PythonCallableCandidate


class PythonParameterReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonCallableCandidate) -> tuple[SourceParameter, ...]:
        raise NotImplementedError


@injectable(as_type=PythonParameterReader)
@dataclass(frozen=True)
class SyntaxParameterReader(PythonParameterReader):
    def read(self, candidate: PythonCallableCandidate) -> tuple[SourceParameter, ...]:
        parameters = self.visit(candidate.node)
        if self.has_receiver(candidate, parameters):
            return parameters[1:]
        return parameters

    def has_receiver(
        self,
        candidate: PythonCallableCandidate,
        parameters: tuple[SourceParameter, ...],
    ) -> bool:
        return (
            bool(candidate.owner_name)
            and self.is_function(candidate.node)
            and not self.has_decorator(candidate.node, "staticmethod")
            and bool(parameters)
            and parameters[0].name in {"self", "cls"}
        )

    @singledispatchmethod
    def is_function(self, node: ast.AST) -> bool:
        return False

    @is_function.register
    def function_is_function(self, node: ast.FunctionDef) -> bool:
        return True

    @is_function.register
    def async_function_is_function(self, node: ast.AsyncFunctionDef) -> bool:
        return True

    @singledispatchmethod
    def visit(self, node: ast.AST) -> tuple[SourceParameter, ...]:
        return ()

    @visit.register
    def visit_FunctionDef(self, node: ast.FunctionDef) -> tuple[SourceParameter, ...]:
        return self.arguments(node.args)

    @visit.register
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> tuple[SourceParameter, ...]:
        return self.arguments(node.args)

    @visit.register
    def visit_Lambda(self, node: ast.Lambda) -> tuple[SourceParameter, ...]:
        return self.arguments(node.args)

    def arguments(self, arguments: ast.arguments) -> tuple[SourceParameter, ...]:
        positional = [*arguments.posonlyargs, *arguments.args]
        required_count = len(positional) - len(arguments.defaults)
        parameters = [
            SourceParameter(
                name=argument.arg,
                annotation=self.argument_annotation(argument),
                kind="positional",
                has_default=index >= required_count,
            )
            for index, argument in enumerate(positional)
        ]
        if arguments.vararg is not None:
            parameters.append(
                SourceParameter(
                    name=arguments.vararg.arg,
                    annotation=self.argument_annotation(arguments.vararg),
                    kind="variadic_positional",
                    has_default=True,
                )
            )
        parameters.extend(
            SourceParameter(
                name=argument.arg,
                annotation=self.argument_annotation(argument),
                kind="named_only",
                has_default=default is not None,
            )
            for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
        )
        if arguments.kwarg is not None:
            parameters.append(
                SourceParameter(
                    name=arguments.kwarg.arg,
                    annotation=self.argument_annotation(arguments.kwarg),
                    kind="variadic_named",
                    has_default=True,
                )
            )
        return tuple(parameters)

    @singledispatchmethod
    def has_decorator(self, node: ast.AST, name: str) -> bool:
        return False

    @has_decorator.register
    def function_has_decorator(self, node: ast.FunctionDef, name: str) -> bool:
        return any(ast.unparse(decorator).rsplit(".", 1)[-1] == name for decorator in node.decorator_list)

    @has_decorator.register
    def async_function_has_decorator(self, node: ast.AsyncFunctionDef, name: str) -> bool:
        return any(ast.unparse(decorator).rsplit(".", 1)[-1] == name for decorator in node.decorator_list)

    def argument_annotation(self, argument: ast.arg) -> str:
        if argument.annotation is None:
            return ""
        return ast.unparse(argument.annotation)
