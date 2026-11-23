import ast
from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_placement import SourcePlacement
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.source_types.absent import SourceTypeAbsent
from ......shared.code.models.source_types.reference import SourceTypeReference
from ......shared.code.models.source_types.unsupported import SourceTypeUnsupported
from ......shared.code.models.values.source_assigned_value import SourceAssignedValue
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ......shared.code.models.values.source_member_kind import SourceMemberKind
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.property_candidate import PythonPropertyCandidate


class PythonPropertyRule(ABC):
    @cached_property
    def is_class_target_dispatch(self) -> Callable[[ast.AST], bool]:
        return self.is_class_target

    @cached_property
    def annotation_is_optional_dispatch(self) -> Callable[[ast.expr], bool]:
        return self.annotation_is_optional

    @cached_property
    def annotation_name_dispatch(self) -> Callable[[ast.expr], str]:
        return self.annotation_name

    @cached_property
    def annotated_type_is_optional_dispatch(self) -> Callable[[ast.expr], bool]:
        return self.annotated_type_is_optional

    @cached_property
    def is_union_dispatch(self) -> Callable[[ast.operator], bool]:
        return self.is_union

    @cached_property
    def value_is_none_dispatch(self) -> Callable[[ast.expr], bool]:
        return self.value_is_none

    @cached_property
    def expression_name_dispatch(self) -> Callable[[ast.expr], str]:
        return self.expression_name

    @cached_property
    def optional_parameters_dispatch(self) -> Callable[[ast.AST], set[str]]:
        return self.optional_parameters

    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        raise NotImplementedError

    def build(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
        is_optional: bool,
        type: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
        visibility: SourceVisibility,
        assigned_value: SourceAssignedValue,
    ) -> SourceClassProperty:
        return SourceClassProperty(
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            name=candidate.name,
            is_optional=is_optional,
            type=type,
            visibility=visibility,
            member_kind=member_kind,
            placement=placement,
            assigned_values=(assigned_value,),
        )

    @singledispatchmethod
    def is_class_target(self, target: ast.AST) -> bool:
        return False

    @is_class_target.register
    def class_target(self, target: ast.Name) -> bool:
        return True

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
        constructor = self.annotation_name_dispatch(node.value)
        if constructor == "Optional":
            return True
        if constructor == "Union":
            return self.annotation_is_optional_dispatch(node.slice)
        if constructor == "Annotated":
            return self.annotated_type_is_optional_dispatch(node.slice)
        return False

    @annotation_is_optional.register
    def union_annotation_is_optional(self, node: ast.BinOp) -> bool:
        return self.is_union_dispatch(node.op) and (
            self.annotation_is_optional_dispatch(node.left) or self.annotation_is_optional_dispatch(node.right)
        )

    @annotation_is_optional.register
    def tuple_annotation_is_optional(self, node: ast.Tuple) -> bool:
        return any(self.annotation_is_optional_dispatch(item) for item in node.elts)

    @singledispatchmethod
    def annotation_name(self, node: ast.expr) -> str:
        return ""

    @annotation_name.register
    def named_annotation_name(self, node: ast.Name) -> str:
        return node.id

    @annotation_name.register
    def qualified_annotation_name(self, node: ast.Attribute) -> str:
        return node.attr

    @singledispatchmethod
    def annotated_type_is_optional(self, node: ast.expr) -> bool:
        return self.annotation_is_optional_dispatch(node)

    @annotated_type_is_optional.register
    def annotated_arguments_type_is_optional(self, node: ast.Tuple) -> bool:
        return bool(node.elts) and self.annotation_is_optional_dispatch(node.elts[0])

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
            if argument.annotation is not None and self.annotation_is_optional_dispatch(argument.annotation)
        }
        optional.update(name for name, default in defaults_by_name.items() if self.value_is_none_dispatch(default))
        optional.update(
            argument.arg
            for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
            if default is not None and self.value_is_none_dispatch(default)
        )
        return optional


class PythonPropertyClassifier(ABC):
    @abstractmethod
    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        raise NotImplementedError


@injectable(as_type=PythonPropertyClassifier)
@dataclass(frozen=True)
class OrderedPythonPropertyClassifier(PythonPropertyClassifier):
    rules: Mapping[Hashable, PythonPropertyRule]

    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate, declaration_id, owner_declaration_id, member_kind, placement)
        raise ExtractorInvariantError(ExtractorInvariantViolation.UNCLASSIFIED_PROPERTY, candidate.name)
