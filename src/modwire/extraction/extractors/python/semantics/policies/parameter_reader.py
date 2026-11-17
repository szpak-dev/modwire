import ast
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ......shared.code.models.callables.source_parameter import SourceParameter
from ......shared.code.models.callables.source_parameter_kind import SourceParameterKind
from ...observations.callable_candidate import PythonCallableCandidate
from .source_type_reader import PythonSourceTypeReader


class PythonParameterReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonCallableCandidate, kind: SourceCallableKind) -> tuple[SourceParameter, ...]:
        raise NotImplementedError


@injectable(as_type=PythonParameterReader)
@dataclass(frozen=True)
class SyntaxParameterReader(PythonParameterReader):
    types: PythonSourceTypeReader

    @cached_property
    def visit_dispatch(self) -> Callable[[ast.AST], tuple[SourceParameter, ...]]:
        return self.visit

    def read(self, candidate: PythonCallableCandidate, kind: SourceCallableKind) -> tuple[SourceParameter, ...]:
        parameters = self.visit_dispatch(candidate.node)
        if (
            kind
            in {
                SourceCallableKind.INSTANCE_METHOD,
                SourceCallableKind.TYPE_METHOD,
                SourceCallableKind.CONSTRUCTOR,
            }
            and parameters
            and parameters[0].kind is SourceParameterKind.POSITIONAL
        ):
            return parameters[1:]
        return parameters

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
                type=self.types.read(argument.annotation),
                kind=SourceParameterKind.POSITIONAL,
                has_default=index >= required_count,
            )
            for index, argument in enumerate(positional)
        ]
        if arguments.vararg is not None:
            parameters.append(
                SourceParameter(
                    name=arguments.vararg.arg,
                    type=self.types.read(arguments.vararg.annotation),
                    kind=SourceParameterKind.VARIADIC_POSITIONAL,
                    has_default=True,
                )
            )
        parameters.extend(
            SourceParameter(
                name=argument.arg,
                type=self.types.read(argument.annotation),
                kind=SourceParameterKind.NAMED_ONLY,
                has_default=default is not None,
            )
            for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
        )
        if arguments.kwarg is not None:
            parameters.append(
                SourceParameter(
                    name=arguments.kwarg.arg,
                    type=self.types.read(arguments.kwarg.annotation),
                    kind=SourceParameterKind.VARIADIC_NAMED,
                    has_default=True,
                )
            )
        return tuple(parameters)
