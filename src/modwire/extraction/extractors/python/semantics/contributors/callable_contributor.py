import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.source_callable import SourceCallable
from ......shared.code.models.types import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..callables.classifier import PythonCallableClassifier
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.annotation_reader import PythonAnnotationReader
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.parameter_reader import PythonParameterReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="10-callable")
@dataclass(frozen=True)
class CallableSemanticContributor(PythonSemanticContributor):
    callables: PythonCallableClassifier
    visibility: PythonVisibilityPolicy
    identities: PythonDeclarationIdentityFactory
    parameters: PythonParameterReader
    annotations: PythonAnnotationReader

    @property
    def order(self) -> int:
        return 10

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        return PythonSemanticContribution(
            callables=tuple(self.source_callable(candidate, context) for candidate in observation.callables)
        )

    def source_callable(self, candidate: PythonCallableCandidate, context: PythonSourceContext) -> SourceCallable:
        kind = self.callables.classify(candidate)
        parameters = self.parameters.read(candidate)
        line_end = candidate.node.end_lineno
        if line_end is None:
            raise ValueError("Python callable requires an end line.")
        return SourceCallable(
            declaration_id=self.identities.create(
                context.source_id,
                self.family(kind),
                candidate.qualified_name,
                candidate.identity_node.lineno,
                candidate.identity_node.col_offset,
            ),
            id=f"{context.source_id}::{candidate.qualified_name}",
            source_id=context.source_id,
            name=candidate.name,
            qualified_name=candidate.qualified_name,
            owner_name=candidate.owner_name,
            kind=kind,
            visibility="public",
            visibility_intent=self.visibility.classify(candidate.name),
            declaration_annotations=[],
            line_start=candidate.node.lineno,
            line_end=line_end,
            line_count=line_end - candidate.node.lineno + 1,
            parameters=list(parameters),
            declared_args=len(parameters),
            optional_args=sum(1 for parameter in parameters if parameter.has_default),
            return_annotation=self.annotations.read(candidate),
            decorators=list(self.decorators(candidate.node)),
            docstring=self.docstring(candidate.node),
        )

    def family(self, kind: SourceCallableKind) -> DeclarationFamily:
        if kind in {"instance_method", "type_method", "static_method", "constructor"}:
            return DeclarationFamily.METHOD
        if kind == "callable_value":
            return DeclarationFamily.VALUE
        if kind == "anonymous":
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
