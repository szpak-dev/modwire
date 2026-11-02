import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_class_method import SourceClassMethod
from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_declaration import SourceDeclaration
from ......shared.code.models.declarations.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.class_candidate import PythonClassCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..classes.classifier import PythonClassClassifier
from ..contribution import PythonSemanticContribution
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="30-class")
@dataclass(frozen=True)
class ClassSemanticContributor(PythonSemanticContributor):
    classes: PythonClassClassifier
    visibility: PythonVisibilityPolicy
    identities: PythonDeclarationIdentityFactory

    @property
    def order(self) -> int:
        return 30

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        declarations: list[SourceDeclaration] = []
        for candidate in observation.classes:
            family = self.classes.classify(candidate)
            class_id = self.identities.create(
                context.source_id,
                family,
                candidate.node.name,
                candidate.node.lineno,
                candidate.node.col_offset,
            )
            properties: tuple[SourceClassProperty, ...] = ()
            if str(class_id.ordinal) in catalog.properties:
                properties = catalog.properties[str(class_id.ordinal)]
            property_names = {item.name for item in properties}
            methods = tuple(
                item
                for item in catalog.methods
                if item.owner_declaration_id == class_id and item.name not in property_names
            )
            if family is DeclarationFamily.ABSTRACT_CLASS:
                declarations.append(self.abstract_class(candidate, class_id, methods, properties))
            else:
                declarations.append(self.concrete_class(candidate, class_id, methods, properties))
        return PythonSemanticContribution(declarations=tuple(declarations))

    def concrete_class(
        self,
        candidate: PythonClassCandidate,
        declaration_id: DeclarationIdentity,
        methods: tuple[SourceClassMethod, ...],
        properties: tuple[SourceClassProperty, ...],
    ) -> SourceDeclaration:
        return SourceDeclaration(
            declaration_id=declaration_id,
            kind=SourceSymbolKind.CLASS,
            name=candidate.node.name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=tuple(ast.unparse(item) for item in candidate.node.decorator_list),
            methods=methods,
            properties=properties,
            line_count=self.line_count(candidate.node),
        )

    def abstract_class(
        self,
        candidate: PythonClassCandidate,
        declaration_id: DeclarationIdentity,
        methods: tuple[SourceClassMethod, ...],
        properties: tuple[SourceClassProperty, ...],
    ) -> SourceDeclaration:
        abstract_names: set[str] = set()
        for statement in candidate.node.body:
            name = self.abstract_method_name(statement)
            if name:
                abstract_names.add(name)
        return SourceDeclaration(
            declaration_id=declaration_id,
            kind=SourceSymbolKind.ABSTRACT_CLASS,
            name=candidate.node.name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=tuple(ast.unparse(item) for item in candidate.node.decorator_list),
            abstract_methods=tuple(item for item in methods if item.name in abstract_names),
            methods=tuple(item for item in methods if item.name not in abstract_names),
            properties=properties,
            line_count=self.line_count(candidate.node),
        )

    @singledispatchmethod
    def abstract_method_name(self, statement: ast.stmt) -> str:
        return ""

    @abstract_method_name.register
    def function_abstract_method_name(self, statement: ast.FunctionDef) -> str:
        if any(ast.unparse(item).rsplit(".", 1)[-1] == "abstractmethod" for item in statement.decorator_list):
            return statement.name
        return ""

    @abstract_method_name.register
    def async_function_abstract_method_name(self, statement: ast.AsyncFunctionDef) -> str:
        if any(ast.unparse(item).rsplit(".", 1)[-1] == "abstractmethod" for item in statement.decorator_list):
            return statement.name
        return ""

    def line_count(self, node: ast.ClassDef) -> int:
        line_end = node.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(ExtractorInvariantViolation.MISSING_CLASS_END_LINE, node.name)
        return line_end - node.lineno + 1
