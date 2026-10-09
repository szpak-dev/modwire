import ast
from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_assigned_value import SourceAssignedValue
from ......shared.code.models.source_class_property import SourceClassProperty
from ......shared.code.models.source_member_kind import SourceMemberKind
from ......shared.code.models.source_visibility import SourceVisibility
from ...observations.property_candidate import PythonPropertyCandidate


class PythonPropertyRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        raise NotImplementedError

    def build(
        self,
        candidate: PythonPropertyCandidate,
        is_optional: bool,
        annotation: str,
        visibility: SourceVisibility,
        member_kind: SourceMemberKind,
        assigned_value: SourceAssignedValue,
    ) -> SourceClassProperty:
        return SourceClassProperty(
            name=candidate.name,
            is_optional=is_optional,
            annotation=annotation,
            visibility=visibility,
            member_kind=member_kind,
            assigned_values=(assigned_value,),
        )

    @singledispatchmethod
    def annotation_is_optional(self, node: ast.expr) -> bool:
        return False

    @annotation_is_optional.register
    def constant_annotation_is_optional(self, node: ast.Constant) -> bool:
        return node.value is None

    @annotation_is_optional.register
    def name_annotation_is_optional(self, node: ast.Name) -> bool:
        return node.id in {"None", "Optional"}

    @annotation_is_optional.register
    def attribute_annotation_is_optional(self, node: ast.Attribute) -> bool:
        return node.attr == "Optional"

    @annotation_is_optional.register
    def subscript_annotation_is_optional(self, node: ast.Subscript) -> bool:
        return self.annotation_is_optional(node.value) or self.annotation_is_optional(node.slice)

    @annotation_is_optional.register
    def union_annotation_is_optional(self, node: ast.BinOp) -> bool:
        return self.is_union(node.op) and (
            self.annotation_is_optional(node.left) or self.annotation_is_optional(node.right)
        )

    @annotation_is_optional.register
    def tuple_annotation_is_optional(self, node: ast.Tuple) -> bool:
        return any(self.annotation_is_optional(item) for item in node.elts)

    @singledispatchmethod
    def is_union(self, operator: ast.operator) -> bool:
        return False

    @is_union.register
    def bit_or_is_union(self, operator: ast.BitOr) -> bool:
        return True

    @singledispatchmethod
    def value_is_none(self, node: ast.expr) -> bool:
        return False

    @value_is_none.register
    def constant_value_is_none(self, node: ast.Constant) -> bool:
        return node.value is None

    @singledispatchmethod
    def expression_name(self, node: ast.expr) -> str:
        return ""

    @expression_name.register
    def named_expression_name(self, node: ast.Name) -> str:
        return node.id

    @singledispatchmethod
    def optional_parameters(self, node: ast.AST) -> set[str]:
        return set()

    @optional_parameters.register
    def function_optional_parameters(self, node: ast.FunctionDef) -> set[str]:
        return self.argument_optional_parameters(node.args)

    @optional_parameters.register
    def async_function_optional_parameters(self, node: ast.AsyncFunctionDef) -> set[str]:
        return self.argument_optional_parameters(node.args)

    def argument_optional_parameters(self, arguments: ast.arguments) -> set[str]:
        positional = [*arguments.posonlyargs, *arguments.args]
        defaults_by_name = (
            {
                argument.arg: default
                for argument, default in zip(positional[-len(arguments.defaults) :], arguments.defaults, strict=True)
            }
            if arguments.defaults
            else {}
        )
        optional = {
            argument.arg
            for argument in [*positional, *arguments.kwonlyargs]
            if argument.annotation is not None and self.annotation_is_optional(argument.annotation)
        }
        optional.update(name for name, default in defaults_by_name.items() if self.value_is_none(default))
        optional.update(
            argument.arg
            for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
            if default is not None and self.value_is_none(default)
        )
        return optional


class PythonPropertyClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        raise NotImplementedError


@injectable(as_type=PythonPropertyClassifier)
@dataclass(frozen=True)
class OrderedPythonPropertyClassifier(PythonPropertyClassifier):
    rules: Mapping[Hashable, PythonPropertyRule]

    def classify(self, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ValueError("No Python property rule accepted the candidate.")
