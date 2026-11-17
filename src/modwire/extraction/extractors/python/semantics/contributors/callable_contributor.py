import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ......shared.code.models.callables.source_callable_value import SourceCallableValue
from ......shared.code.models.callables.source_class_method import SourceClassMethod
from ......shared.code.models.callables.source_function import SourceFunction
from ......shared.code.models.declarations.source_scope_kind import SourceScopeKind
from ......shared.code.models.declarations.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.values.source_value_declaration_kind import SourceValueDeclarationKind
from ......shared.code.models.values.source_value_scope import SourceValueScope
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.parameter_reader import PythonParameterReader
from ..policies.source_type_reader import PythonSourceTypeReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="10-callable")
@dataclass(frozen=True)
class CallableSemanticContributor(PythonSemanticContributor):
    visibility: PythonVisibilityPolicy
    parameters: PythonParameterReader
    types: PythonSourceTypeReader

    @cached_property
    def decorators_dispatch(self) -> Callable[[ast.AST], tuple[str, ...]]:
        return self.decorators

    @cached_property
    def docstring_dispatch(self) -> Callable[[ast.AST], str]:
        return self.docstring

    @cached_property
    def return_annotation_dispatch(self) -> Callable[[ast.AST], ast.expr | None]:
        return self.return_annotation

    @property
    def order(self) -> int:
        return 10

    def contribute(
        self, observation: PythonSourceObservation, catalog: PythonSemanticCatalog, context: PythonSourceContext
    ) -> PythonSemanticContribution:
        functions: list[SourceFunction] = []
        methods: list[SourceClassMethod] = []
        values: list[SourceCallableValue] = []
        anonymous: list[SourceAnonymousCallable] = []
        for candidate in observation.callables:
            kind = catalog.callable_kinds[candidate.node]
            start, end = candidate.source_span
            visibility_intent = self.visibility.classify(candidate.name)
            parameters = self.parameters.read(candidate, kind)
            return_type = self.types.read(self.return_annotation_dispatch(candidate.node))
            decorators = self.decorators_dispatch(candidate.node)
            docstring = self.docstring_dispatch(candidate.node)
            placement = catalog.placement(candidate.binding_scope)
            if kind is SourceCallableKind.FUNCTION:
                functions.append(
                    SourceFunction(
                        declaration_id=catalog.scope_identities[candidate.node],
                        source_id=context.source_id,
                        name=candidate.name,
                        qualified_name=candidate.qualified_name,
                        kind=kind,
                        visibility=SourceVisibility.PUBLIC,
                        visibility_intent=visibility_intent,
                        declaration_annotations=(),
                        line_start=start,
                        line_end=end,
                        line_count=end - start + 1,
                        parameters=parameters,
                        return_type=return_type,
                        decorators=decorators,
                        docstring=docstring,
                        placement=placement,
                    )
                )
            elif kind is SourceCallableKind.CALLABLE_VALUE:
                values.append(
                    SourceCallableValue(
                        declaration_id=catalog.scope_identities[candidate.node],
                        source_id=context.source_id,
                        name=candidate.name,
                        qualified_name=candidate.qualified_name,
                        kind=kind,
                        visibility=SourceVisibility.PUBLIC,
                        visibility_intent=visibility_intent,
                        declaration_annotations=(),
                        line_start=start,
                        line_end=end,
                        line_count=end - start + 1,
                        parameters=parameters,
                        return_type=return_type,
                        decorators=decorators,
                        docstring=docstring,
                        placement=placement,
                        declaration_kind=SourceValueDeclarationKind.ASSIGNMENT,
                        value_kind=SourceSymbolKind.VALUE_CALLABLE,
                        scope=SourceValueScope.MODULE
                        if placement.lexical_scope.kind is SourceScopeKind.FILE
                        else SourceValueScope.LOCAL,
                    )
                )
            elif kind is SourceCallableKind.ANONYMOUS:
                anonymous.append(
                    SourceAnonymousCallable(
                        declaration_id=catalog.scope_identities[candidate.node],
                        source_id=context.source_id,
                        name=candidate.name,
                        qualified_name=candidate.qualified_name,
                        kind=kind,
                        visibility=SourceVisibility.PUBLIC,
                        visibility_intent=visibility_intent,
                        declaration_annotations=(),
                        line_start=start,
                        line_end=end,
                        line_count=end - start + 1,
                        parameters=parameters,
                        return_type=return_type,
                        decorators=decorators,
                        docstring=docstring,
                        placement=placement,
                    )
                )
            else:
                methods.append(
                    SourceClassMethod(
                        declaration_id=catalog.scope_identities[candidate.node],
                        source_id=context.source_id,
                        name=candidate.name,
                        qualified_name=candidate.qualified_name,
                        kind=kind,
                        visibility=SourceVisibility.PUBLIC,
                        visibility_intent=visibility_intent,
                        declaration_annotations=(),
                        line_start=start,
                        line_end=end,
                        line_count=end - start + 1,
                        parameters=parameters,
                        return_type=return_type,
                        decorators=decorators,
                        docstring=docstring,
                        placement=placement,
                        owner_declaration_id=catalog.scope_identities[candidate.binding_scope],
                    )
                )
        return PythonSemanticContribution(
            functions=tuple(functions),
            methods=tuple(methods),
            callable_values=tuple(values),
            anonymous_callables=tuple(anonymous),
        )

    @singledispatchmethod
    def decorators(self, node: ast.AST) -> tuple[str, ...]:
        return ()

    @decorators.register
    def function_decorators(self, node: ast.FunctionDef) -> tuple[str, ...]:
        return tuple(ast.unparse(item) for item in node.decorator_list)

    @decorators.register
    def async_function_decorators(self, node: ast.AsyncFunctionDef) -> tuple[str, ...]:
        return tuple(ast.unparse(item) for item in node.decorator_list)

    @singledispatchmethod
    def docstring(self, node: ast.AST) -> str:
        return ""

    @docstring.register
    def function_docstring(self, node: ast.FunctionDef) -> str:
        return ast.get_docstring(node) or ""

    @docstring.register
    def async_function_docstring(self, node: ast.AsyncFunctionDef) -> str:
        return ast.get_docstring(node) or ""

    @singledispatchmethod
    def return_annotation(self, node: ast.AST) -> ast.expr | None:
        return None

    @return_annotation.register
    def function_return_annotation(self, node: ast.FunctionDef) -> ast.expr | None:
        return node.returns

    @return_annotation.register
    def async_function_return_annotation(self, node: ast.AsyncFunctionDef) -> ast.expr | None:
        return node.returns
