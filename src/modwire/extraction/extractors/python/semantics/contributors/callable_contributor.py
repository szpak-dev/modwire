import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ......shared.code.models.callables.source_callable_value import SourceCallableValue
from ......shared.code.models.callables.source_class_method import SourceClassMethod
from ......shared.code.models.callables.source_function import SourceFunction
from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.values.source_value_declaration_kind import SourceValueDeclarationKind
from ......shared.code.models.values.source_value_scope import SourceValueScope
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.callable_candidate import PythonCallableCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..callables.classifier import PythonCallableClassifier
from ..catalog import PythonSemanticCatalog
from ..classes.classifier import PythonClassClassifier
from ..contribution import PythonSemanticContribution
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.parameter_reader import PythonParameterReader
from ..policies.source_type_reader import PythonSourceTypeReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="10-callable")
@dataclass(frozen=True)
class CallableSemanticContributor(PythonSemanticContributor):
    callables: PythonCallableClassifier
    classes: PythonClassClassifier
    visibility: PythonVisibilityPolicy
    identities: PythonDeclarationIdentityFactory
    parameters: PythonParameterReader
    types: PythonSourceTypeReader

    @property
    def order(self) -> int:
        return 10

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        owners = {
            candidate.node.name: self.identities.create(
                context.source_id,
                self.classes.classify(candidate),
                candidate.node.name,
                candidate.node.lineno,
                candidate.node.col_offset,
            )
            for candidate in observation.classes
        }
        functions: list[SourceFunction] = []
        methods: list[SourceClassMethod] = []
        callable_values: list[SourceCallableValue] = []
        anonymous_callables: list[SourceAnonymousCallable] = []
        for candidate in observation.callables:
            kind = self.callables.classify(candidate)
            if kind is SourceCallableKind.FUNCTION:
                functions.append(self.source_function(candidate, context))
            elif kind in {
                SourceCallableKind.INSTANCE_METHOD,
                SourceCallableKind.TYPE_METHOD,
                SourceCallableKind.STATIC_METHOD,
                SourceCallableKind.CONSTRUCTOR,
            }:
                if not candidate.owner_name:
                    raise ExtractorInvariantError(
                        ExtractorInvariantViolation.MISSING_CALLABLE_OWNER,
                        candidate.qualified_name,
                    )
                methods.append(self.source_method(candidate, context, owners[candidate.owner_name], kind))
            elif kind is SourceCallableKind.CALLABLE_VALUE:
                callable_values.append(self.source_callable_value(candidate, context))
            else:
                anonymous_callables.append(self.source_anonymous_callable(candidate, context))
        return PythonSemanticContribution(
            functions=tuple(functions),
            methods=tuple(methods),
            callable_values=tuple(callable_values),
            anonymous_callables=tuple(anonymous_callables),
        )

    def source_function(
        self,
        candidate: PythonCallableCandidate,
        context: PythonSourceContext,
    ) -> SourceFunction:
        line_end = candidate.node.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.MISSING_CALLABLE_END_LINE, candidate.qualified_name
            )
        return SourceFunction(
            declaration_id=self.declaration_id(candidate, context, SourceCallableKind.FUNCTION),
            source_id=context.source_id,
            name=candidate.name,
            qualified_name=candidate.qualified_name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.name),
            declaration_annotations=(),
            line_start=candidate.node.lineno,
            line_end=line_end,
            line_count=line_end - candidate.node.lineno + 1,
            parameters=self.parameters.read(candidate),
            return_type=self.types.read(self.return_annotation(candidate.node)),
            decorators=self.decorators(candidate.node),
            docstring=self.docstring(candidate.node),
        )

    def source_method(
        self,
        candidate: PythonCallableCandidate,
        context: PythonSourceContext,
        owner_declaration_id: DeclarationIdentity,
        kind: SourceCallableKind,
    ) -> SourceClassMethod:
        line_end = candidate.node.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.MISSING_CALLABLE_END_LINE, candidate.qualified_name
            )
        return SourceClassMethod(
            declaration_id=self.declaration_id(candidate, context, kind),
            owner_declaration_id=owner_declaration_id,
            source_id=context.source_id,
            name=candidate.name,
            qualified_name=candidate.qualified_name,
            kind=kind,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.name),
            declaration_annotations=(),
            line_start=candidate.node.lineno,
            line_end=line_end,
            line_count=line_end - candidate.node.lineno + 1,
            parameters=self.parameters.read(candidate),
            return_type=self.types.read(self.return_annotation(candidate.node)),
            decorators=self.decorators(candidate.node),
            docstring=self.docstring(candidate.node),
        )

    def source_callable_value(
        self,
        candidate: PythonCallableCandidate,
        context: PythonSourceContext,
    ) -> SourceCallableValue:
        line_end = candidate.node.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.MISSING_CALLABLE_END_LINE, candidate.qualified_name
            )
        return SourceCallableValue(
            declaration_id=self.declaration_id(candidate, context, SourceCallableKind.CALLABLE_VALUE),
            source_id=context.source_id,
            name=candidate.name,
            qualified_name=candidate.qualified_name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.name),
            declaration_annotations=(),
            line_start=candidate.node.lineno,
            line_end=line_end,
            line_count=line_end - candidate.node.lineno + 1,
            parameters=self.parameters.read(candidate),
            return_type=self.types.read(self.return_annotation(candidate.node)),
            decorators=self.decorators(candidate.node),
            docstring=self.docstring(candidate.node),
            declaration_kind=SourceValueDeclarationKind.ASSIGNMENT,
            value_kind=SourceSymbolKind.VALUE_CALLABLE,
            scope=SourceValueScope.MODULE,
        )

    def source_anonymous_callable(
        self,
        candidate: PythonCallableCandidate,
        context: PythonSourceContext,
    ) -> SourceAnonymousCallable:
        line_end = candidate.node.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.MISSING_CALLABLE_END_LINE, candidate.qualified_name
            )
        return SourceAnonymousCallable(
            declaration_id=self.declaration_id(candidate, context, SourceCallableKind.ANONYMOUS),
            source_id=context.source_id,
            name=candidate.name,
            qualified_name=candidate.qualified_name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.name),
            declaration_annotations=(),
            line_start=candidate.node.lineno,
            line_end=line_end,
            line_count=line_end - candidate.node.lineno + 1,
            parameters=self.parameters.read(candidate),
            return_type=self.types.read(self.return_annotation(candidate.node)),
            decorators=self.decorators(candidate.node),
            docstring=self.docstring(candidate.node),
        )

    def declaration_id(
        self,
        candidate: PythonCallableCandidate,
        context: PythonSourceContext,
        kind: SourceCallableKind,
    ) -> DeclarationIdentity:
        return self.identities.create(
            context.source_id,
            self.family(kind),
            candidate.qualified_name,
            candidate.identity_node.lineno,
            candidate.identity_node.col_offset,
        )

    def family(self, kind: SourceCallableKind) -> DeclarationFamily:
        if kind in {
            SourceCallableKind.INSTANCE_METHOD,
            SourceCallableKind.TYPE_METHOD,
            SourceCallableKind.STATIC_METHOD,
            SourceCallableKind.CONSTRUCTOR,
        }:
            return DeclarationFamily.METHOD
        if kind is SourceCallableKind.CALLABLE_VALUE:
            return DeclarationFamily.VALUE
        if kind is SourceCallableKind.ANONYMOUS:
            return DeclarationFamily.CALLABLE
        return DeclarationFamily.FUNCTION

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
