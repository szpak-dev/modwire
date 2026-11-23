import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_types.absent import SourceTypeAbsent
from ......shared.code.models.source_types.reference import SourceTypeReference
from ......shared.code.models.source_types.unsupported import SourceTypeUnsupported


@injectable
@dataclass(frozen=True)
class PythonSourceTypeReader:
    @cached_property
    def visit_dispatch(self) -> Callable[[ast.expr], SourceTypeReference | SourceTypeUnsupported]:
        return self.visit

    @cached_property
    def reference_name_dispatch(self) -> Callable[[ast.expr], str]:
        return self.reference_name

    @cached_property
    def arguments_dispatch(self) -> Callable[[ast.expr], tuple[ast.expr, ...]]:
        return self.arguments

    def read(
        self,
        annotation: ast.expr | None,
    ) -> SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported:
        if annotation is None:
            return SourceTypeAbsent()
        return self.visit_dispatch(annotation)

    @singledispatchmethod
    def visit(self, annotation: ast.expr) -> SourceTypeReference | SourceTypeUnsupported:
        return SourceTypeUnsupported()

    @visit.register
    def visit_name(self, annotation: ast.Name) -> SourceTypeReference:
        return SourceTypeReference(name=annotation.id)

    @visit.register
    def visit_attribute(self, annotation: ast.Attribute) -> SourceTypeReference:
        return SourceTypeReference(name=ast.unparse(annotation))

    @visit.register
    def visit_subscript(self, annotation: ast.Subscript) -> SourceTypeReference | SourceTypeUnsupported:
        name = self.reference_name_dispatch(annotation.value)
        if not name:
            return SourceTypeUnsupported()
        arguments = self.arguments_dispatch(annotation.slice)
        return SourceTypeReference(name=name, arguments=tuple(self.visit_dispatch(argument) for argument in arguments))

    @visit.register
    def visit_constant(self, annotation: ast.Constant) -> SourceTypeReference | SourceTypeUnsupported:
        if annotation.value is None:
            return SourceTypeReference(name="None")
        return SourceTypeUnsupported()

    @singledispatchmethod
    def reference_name(self, annotation: ast.expr) -> str:
        return ""

    @reference_name.register
    def name_reference_name(self, annotation: ast.Name) -> str:
        return annotation.id

    @reference_name.register
    def attribute_reference_name(self, annotation: ast.Attribute) -> str:
        return ast.unparse(annotation)

    @singledispatchmethod
    def arguments(self, annotation: ast.expr) -> tuple[ast.expr, ...]:
        return (annotation,)

    @arguments.register
    def tuple_arguments(self, annotation: ast.Tuple) -> tuple[ast.expr, ...]:
        return tuple(annotation.elts)
