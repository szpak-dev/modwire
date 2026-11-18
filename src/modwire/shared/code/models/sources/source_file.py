from collections.abc import Mapping
from functools import cached_property
from typing import Self, assert_never

from pydantic import Field, model_validator

from ....values.models.value_model import ValueModel
from ..callables.source_anonymous_callable import SourceAnonymousCallable
from ..callables.source_call import SourceCall
from ..callables.source_callable import SourceCallable
from ..callables.source_callable_value import SourceCallableValue
from ..callables.source_function import SourceFunction
from ..callables.source_unresolved_method import SourceUnresolvedMethod
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_binding_kind import SourceBindingKind
from ..declarations.source_declaration import SourceDeclaration
from ..declarations.source_declaration_relation import SourceDeclarationRelation
from ..declarations.source_namespace import SourceNamespace
from ..declarations.source_namespace_membership import SourceNamespaceMembership
from ..declarations.source_namespace_membership_kind import SourceNamespaceMembershipKind
from ..declarations.source_no_namespace import SourceNoNamespace
from ..declarations.source_placement import SourcePlacement
from ..declarations.source_scope_kind import SourceScopeKind
from ..declarations.source_symbol_kind import SourceSymbolKind
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..inventories.file_inventory_coverage import FileInventoryCoverage
from ..values.source_class_property import SourceClassProperty
from ..values.source_value import SourceValue
from .identity import FileId, ImportIdentity
from .source_export import SourceExport
from .source_import import SourceImport


class SourceFile(ValueModel):
    file_id: FileId
    import_identity: ImportIdentity
    imports: list[SourceImport]
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...]
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callable_values: tuple[SourceCallableValue, ...] = Field(default_factory=tuple)
    anonymous_callables: tuple[SourceAnonymousCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = Field(default_factory=tuple)
    unresolved_methods: tuple[SourceUnresolvedMethod, ...]
    inventory: FileInventoryCoverage
    line_count: int
    code_line_count: int
    public_symbol_count: int

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        return self.validate_facts()

    def validate_facts(self) -> Self:
        self.validate_declaration_identities()
        self.validate_inventory()
        self.validate_placement()
        self.validate_bindings()
        return self

    def validate_declaration_identities(self) -> Self:
        declarations_by_family = (
            (self.declarations, None),
            (self.functions, DeclarationFamily.FUNCTION),
            (self.values, DeclarationFamily.VALUE),
        )
        for declarations, family in declarations_by_family:
            if family is not None and any(item.declaration_id.family is not family for item in declarations):
                raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_FAMILY, str(self.file_id))
        if any(self.declaration_family(item.kind) is not item.declaration_id.family for item in self.declarations):
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_KIND, str(self.file_id))
        callables = self.canonical_callables()
        callable_identities = {item.declaration_id for item in callables}
        call_ordinals: dict[DeclarationIdentity, list[int]] = {}
        foreign_source = False
        if self.calls:
            source = self.calls[0].source_callable_id
            ordinals = call_ordinals[source] = list[int]()
            for item in self.calls:
                if item.source_id != self.file_id:
                    foreign_source = True
                if item.source_callable_id is not source:
                    source = item.source_callable_id
                    ordinals = call_ordinals.setdefault(source, list[int]())
                ordinals.append(item.ordinal)
        if any(len(set(ordinals)) != len(ordinals) for ordinals in call_ordinals.values()):
            raise CodeValidationError(CodeViolation.DUPLICATE_CALL, str(self.file_id))
        if foreign_source or any(identity.source_id != self.file_id for identity in call_ordinals):
            raise CodeValidationError(CodeViolation.FOREIGN_CALL_SOURCE, str(self.file_id))
        if any(identity not in callable_identities for identity in call_ordinals):
            raise CodeValidationError(CodeViolation.UNKNOWN_CALL_SOURCE_CALLABLE, str(self.file_id))
        declaration_identities = {item.declaration_id for item in self.declarations}
        if any(relation.source_declaration_id not in declaration_identities for relation in self.declaration_relations):
            raise CodeValidationError(CodeViolation.UNKNOWN_DECLARATION_RELATION_SOURCE, str(self.file_id))
        return self

    def canonical_callables(self) -> tuple[SourceCallable, ...]:
        return self.callable_inventory

    @cached_property
    def callable_inventory(self) -> tuple[SourceCallable, ...]:
        callables = (
            *self.functions,
            *(method for declaration in self.declarations for method in declaration.methods),
            *(method for declaration in self.declarations for method in declaration.abstract_methods),
            *self.callable_values,
            *self.anonymous_callables,
            *self.unresolved_methods,
        )
        return tuple(sorted(callables, key=lambda item: item.declaration_id.ordinal))

    def declaration_placements(self) -> tuple[tuple[DeclarationIdentity, SourcePlacement], ...]:
        return tuple((item.declaration_id, item.placement) for item in self.placement_inventory)

    @cached_property
    def placement_inventory(
        self,
    ) -> tuple[SourceDeclaration | SourceNamespace | SourceValue | SourceCallable | SourceClassProperty, ...]:
        return (
            *self.declarations,
            *self.namespaces,
            *self.values,
            *self.canonical_callables(),
            *(member for declaration in self.declarations for member in declaration.properties),
        )

    def validate_inventory(self) -> Self:
        self.inventory.declarations.validate_item_count(len(self.declarations))
        self.inventory.functions.validate_item_count(len(self.functions))
        self.inventory.values.validate_item_count(len(self.values))
        self.inventory.callable_values.validate_item_count(len(self.callable_values))
        self.inventory.anonymous_callables.validate_item_count(len(self.anonymous_callables))
        self.inventory.namespaces.validate_item_count(len(self.namespaces))
        self.inventory.exports.validate_item_count(len(self.exports))
        self.inventory.unresolved_methods.validate_item_count(len(self.unresolved_methods))
        return self

    def validate_placement(self) -> Self:
        placements = self.placement_inventory
        identities = {item.declaration_id: index for index, item in enumerate(placements)}
        if len(identities) != len(placements):
            raise CodeValidationError(CodeViolation.DUPLICATE_DECLARATION_IDENTITY, str(self.file_id))
        if any(identity.source_id != self.file_id for identity in identities):
            raise CodeValidationError(CodeViolation.FOREIGN_DECLARATION_IDENTITY, str(self.file_id))
        if len({identity.content_digest for identity in identities}) > 1:
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_CAPTURE, str(self.file_id))
        if any(item.declaration_id.family is not DeclarationFamily.NAMESPACE for item in self.namespaces):
            raise CodeValidationError(CodeViolation.INVALID_NAMESPACE_TARGET, str(self.file_id))
        scope_parents: dict[int, int | None] = {}
        for item in placements:
            scope = item.placement.lexical_scope
            scope_id = id(scope)
            if scope_id not in scope_parents:
                if scope.kind is SourceScopeKind.BLOCK:
                    if scope.end_utf8_offset <= scope.start_utf8_offset:
                        raise CodeValidationError(CodeViolation.INVALID_BLOCK_SCOPE, item.declaration_id.canonical())
                    scope = scope.container
                parent: int | None = None
                if scope.kind is SourceScopeKind.DECLARATION:
                    parent = identities.get(scope.declaration_id)
                    if parent is None:
                        raise CodeValidationError(CodeViolation.UNKNOWN_LEXICAL_SCOPE, item.declaration_id.canonical())
                scope_parents[scope_id] = parent
        parents = {
            index: parent
            for index in scope_parents.values()
            if index is not None
            if (parent := scope_parents[id(placements[index].placement.lexical_scope)]) is not None
        }
        for index in tuple(parents):
            if index not in parents:
                continue
            visited: set[int] = set()
            current = index
            while current in parents:
                visited.add(current)
                current = parents.pop(current)
            if current in visited:
                raise CodeValidationError(
                    CodeViolation.CYCLIC_LEXICAL_SCOPE, placements[index].declaration_id.canonical()
                )
        return self

    def validate_bindings(self) -> Self:
        placements = self.placement_inventory
        identities = (
            {item.declaration_id for item in placements}
            if self.exports
            or any(relation.target.kind is SourceBindingKind.RESOLVED for relation in self.declaration_relations)
            else set[DeclarationIdentity]()
        )
        namespace_ids = {
            *(item.declaration_id for item in self.namespaces),
            *(item.declaration_id for item in self.declarations if item.kind is SourceSymbolKind.MODULE),
        }
        validated_namespaces: set[int] = set()
        previous_namespace: SourceNoNamespace | SourceNamespaceMembership | None = None
        for item in placements:
            namespace = item.placement.namespace
            if namespace is previous_namespace:
                continue
            previous_namespace = namespace
            namespace_id = id(namespace)
            if namespace_id in validated_namespaces:
                continue
            validated_namespaces.add(namespace_id)
            if (
                namespace.kind is SourceNamespaceMembershipKind.MEMBER
                and namespace.target.kind is SourceBindingKind.RESOLVED
                and namespace.target.declaration_id not in namespace_ids
            ):
                raise CodeValidationError(CodeViolation.INVALID_NAMESPACE_TARGET, item.declaration_id.canonical())
        for export in self.exports:
            if export.binding.kind is SourceBindingKind.RESOLVED:
                if not export.binding.declaration_ids:
                    raise CodeValidationError(CodeViolation.EMPTY_EXPORT_BINDING, export.name)
                if any(identity not in identities for identity in export.binding.declaration_ids):
                    raise CodeValidationError(CodeViolation.UNKNOWN_DECLARATION_TARGET, export.name)
        for relation in self.declaration_relations:
            if relation.target.kind is SourceBindingKind.RESOLVED and relation.target.declaration_id not in identities:
                raise CodeValidationError(CodeViolation.UNKNOWN_DECLARATION_TARGET, relation.target_reference)
        return self

    def model_copy(self, *, update: Mapping[str, object] | None = None, deep: bool = False) -> Self:
        copied = super().model_copy(update=update, deep=deep)
        callables_changed = (
            copied.declarations is not self.declarations
            or copied.functions is not self.functions
            or copied.callable_values is not self.callable_values
            or copied.anonymous_callables is not self.anonymous_callables
            or copied.unresolved_methods is not self.unresolved_methods
        )
        if callables_changed:
            del copied.callable_inventory
            copied.canonical_callables()
        if callables_changed or copied.namespaces is not self.namespaces or copied.values is not self.values:
            del copied.placement_inventory
            _ = copied.placement_inventory
        return copied

    def declaration_family(self, kind: SourceSymbolKind) -> DeclarationFamily:
        if kind is SourceSymbolKind.CLASS or kind is SourceSymbolKind.RECORD or kind is SourceSymbolKind.ENUM:
            return DeclarationFamily.CLASS
        if kind is SourceSymbolKind.MODULE or kind is SourceSymbolKind.TRAIT or kind is SourceSymbolKind.TYPE_ALIAS:
            return DeclarationFamily.TYPE
        if kind is SourceSymbolKind.ABSTRACT_CLASS:
            return DeclarationFamily.ABSTRACT_CLASS
        if kind is SourceSymbolKind.INTERFACE or kind is SourceSymbolKind.ANNOTATION:
            return DeclarationFamily.INTERFACE
        if kind is SourceSymbolKind.FUNCTION:
            return DeclarationFamily.FUNCTION
        if kind is SourceSymbolKind.CALLABLE:
            return DeclarationFamily.CALLABLE
        if (
            kind is SourceSymbolKind.VALUE_CALLABLE
            or kind is SourceSymbolKind.VALUE_CLASS
            or kind is SourceSymbolKind.VALUE_LITERAL
            or kind is SourceSymbolKind.VALUE_OBJECT
            or kind is SourceSymbolKind.VALUE_UNKNOWN
        ):
            return DeclarationFamily.VALUE
        assert_never(kind)
