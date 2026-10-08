import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.source_abstract_class import SourceAbstractClass
from ......shared.code.models.source_class import SourceClass
from ......shared.code.models.source_class_method import SourceClassMethod
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
        classes: list[SourceClass] = []
        abstract_classes: list[SourceAbstractClass] = []
        for candidate in observation.classes:
            family = self.classes.classify(candidate)
            methods = self.class_methods(candidate.node)
            if family is DeclarationFamily.ABSTRACT_CLASS:
                abstract_classes.append(self.abstract_class(candidate, methods, context))
            else:
                classes.append(self.concrete_class(candidate, methods, context))
        return PythonSemanticContribution(classes=tuple(classes), abstract_classes=tuple(abstract_classes))

    def concrete_class(
        self,
        candidate: PythonClassCandidate,
        methods: tuple[SourceClassMethod, ...],
        context: PythonSourceContext,
    ) -> SourceClass:
        return SourceClass(
            declaration_id=self.identities.create(
                context.source_id,
                DeclarationFamily.CLASS,
                candidate.node.name,
                candidate.node.lineno,
                candidate.node.col_offset,
            ),
            name=candidate.node.name,
            visibility="public",
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=[ast.unparse(item) for item in candidate.node.decorator_list],
            methods=list(methods),
            properties=[],
            line_count=self.line_count(candidate.node),
        )

    def abstract_class(
        self,
        candidate: PythonClassCandidate,
        methods: tuple[SourceClassMethod, ...],
        context: PythonSourceContext,
    ) -> SourceAbstractClass:
        abstract_names: set[str] = set()
        for statement in candidate.node.body:
            name = self.abstract_method_name(statement)
            if name:
                abstract_names.add(name)
        return SourceAbstractClass(
            declaration_id=self.identities.create(
                context.source_id,
                DeclarationFamily.ABSTRACT_CLASS,
                candidate.node.name,
                candidate.node.lineno,
                candidate.node.col_offset,
            ),
            name=candidate.node.name,
            visibility="public",
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=[ast.unparse(item) for item in candidate.node.decorator_list],
            abstract_methods=[item for item in methods if item.name in abstract_names],
            concrete_methods=[item for item in methods if item.name not in abstract_names],
            properties=[],
            line_count=self.line_count(candidate.node),
        )

    def class_methods(self, node: ast.ClassDef) -> tuple[SourceClassMethod, ...]:
        return tuple(source_method for statement in node.body for source_method in self.class_method(statement))

    @singledispatchmethod
    def class_method(self, statement: ast.stmt) -> tuple[SourceClassMethod, ...]:
        return ()

    @class_method.register
    def function_class_method(self, statement: ast.FunctionDef) -> tuple[SourceClassMethod, ...]:
        return (self.function_method(statement),)

    @class_method.register
    def async_function_class_method(self, statement: ast.AsyncFunctionDef) -> tuple[SourceClassMethod, ...]:
        return (self.function_method(statement),)

    def function_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> SourceClassMethod:
        declared_args, optional_args = self.argument_counts(node)
        return SourceClassMethod(
            name=node.name,
            visibility="public",
            visibility_intent=self.visibility.classify(node.name),
            declaration_annotations=[],
            line_count=self.function_line_count(node),
            declared_args=declared_args,
            optional_args=optional_args,
        )

    def argument_counts(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]:
        positional = [*node.args.posonlyargs, *node.args.args]
        required_count = len(positional) - len(node.args.defaults)
        parameters = [(argument.arg, index >= required_count) for index, argument in enumerate(positional)]
        parameters.extend(
            (argument.arg, default is not None)
            for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
        )
        if node.args.vararg is not None:
            parameters.append((node.args.vararg.arg, True))
        if node.args.kwarg is not None:
            parameters.append((node.args.kwarg.arg, True))
        if parameters and parameters[0][0] in {"self", "cls"} and not self.has_decorator(node, "staticmethod"):
            parameters = parameters[1:]
        return (len(parameters), sum(is_optional for _, is_optional in parameters))

    def has_decorator(self, node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == name for item in node.decorator_list)

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
            raise ValueError("Python class requires an end line.")
        return line_end - node.lineno + 1

    def function_line_count(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        line_end = node.end_lineno
        if line_end is None:
            raise ValueError("Python function requires an end line.")
        return line_end - node.lineno + 1
