from collections.abc import Mapping
from functools import cached_property
from typing import Self

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
from ..declarations.source_namespace_membership_kind import SourceNamespaceMembershipKind
from ..declarations.source_placement import SourcePlacement
from ..declarations.source_scope_kind import SourceScopeKind
from ..declarations.source_symbol_kind import SourceSymbolKind
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..inventories.file_inventory_coverage import FileInventoryCoverage
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
        callable_identities = {item.declaration_id.canonical() for item in callables}
        call_identities = tuple(item.identity() for item in self.calls)
        if len(call_identities) != len(set(call_identities)):
            raise CodeValidationError(CodeViolation.DUPLICATE_CALL, str(self.file_id))
        if any(
            item.source_id != self.file_id or item.source_callable_id.source_id != self.file_id for item in self.calls
        ):
            raise CodeValidationError(CodeViolation.FOREIGN_CALL_SOURCE, str(self.file_id))
        if any(item.source_callable_id.canonical() not in callable_identities for item in self.calls):
            raise CodeValidationError(CodeViolation.UNKNOWN_CALL_SOURCE_CALLABLE, str(self.file_id))
        declaration_identities = {item.declaration_id.canonical() for item in self.declarations}
        if any(
            relation.source_declaration_id.canonical() not in declaration_identities
            for relation in self.declaration_relations
        ):
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
        return self.placement_inventory

    @cached_property
    def placement_inventory(self) -> tuple[tuple[DeclarationIdentity, SourcePlacement], ...]:
        return tuple(
            (item.declaration_id, item.placement)
            for item in (
                *self.declarations,
                *self.namespaces,
                *self.values,
                *self.canonical_callables(),
                *(member for declaration in self.declarations for member in declaration.properties),
            )
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
        placements = self.declaration_placements()
        identities = {identity for identity, _ in placements}
        if len(identities) != len(placements):
            raise CodeValidationError(CodeViolation.DUPLICATE_DECLARATION_IDENTITY, str(self.file_id))
        if any(identity.source_id != self.file_id for identity in identities):
            raise CodeValidationError(CodeViolation.FOREIGN_DECLARATION_IDENTITY, str(self.file_id))
        if len({identity.content_digest for identity in identities}) > 1:
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_CAPTURE, str(self.file_id))
        if any(item.declaration_id.family is not DeclarationFamily.NAMESPACE for item in self.namespaces):
            raise CodeValidationError(CodeViolation.INVALID_NAMESPACE_TARGET, str(self.file_id))
        parents: dict[DeclarationIdentity, DeclarationIdentity] = {}
        for identity, placement in placements:
            scope = placement.lexical_scope
            if scope.kind is SourceScopeKind.BLOCK:
                if scope.end_utf8_offset <= scope.start_utf8_offset:
                    raise CodeValidationError(CodeViolation.INVALID_BLOCK_SCOPE, identity.canonical())
                scope = scope.container
            if scope.kind is SourceScopeKind.DECLARATION:
                if scope.declaration_id not in identities:
                    raise CodeValidationError(CodeViolation.UNKNOWN_LEXICAL_SCOPE, identity.canonical())
                parents[identity] = scope.declaration_id
        for identity in parents:
            visited: set[DeclarationIdentity] = set()
            current = identity
            while current in parents:
                if current in visited:
                    raise CodeValidationError(CodeViolation.CYCLIC_LEXICAL_SCOPE, identity.canonical())
                visited.add(current)
                current = parents[current]
        return self

    def validate_bindings(self) -> Self:
        placements = self.declaration_placements()
        identities = {identity for identity, _ in placements}
        namespace_ids = {
            *(item.declaration_id for item in self.namespaces),
            *(item.declaration_id for item in self.declarations if item.kind is SourceSymbolKind.MODULE),
        }
        for identity, placement in placements:
            namespace = placement.namespace
            if (
                namespace.kind is SourceNamespaceMembershipKind.MEMBER
                and namespace.target.kind is SourceBindingKind.RESOLVED
                and namespace.target.declaration_id not in namespace_ids
            ):
                raise CodeValidationError(CodeViolation.INVALID_NAMESPACE_TARGET, identity.canonical())
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
            copied.declaration_placements()
        return copied

    def declaration_family(self, kind: SourceSymbolKind) -> DeclarationFamily:
        return {
            SourceSymbolKind.CLASS: DeclarationFamily.CLASS,
            SourceSymbolKind.RECORD: DeclarationFamily.CLASS,
            SourceSymbolKind.ENUM: DeclarationFamily.CLASS,
            SourceSymbolKind.ABSTRACT_CLASS: DeclarationFamily.ABSTRACT_CLASS,
            SourceSymbolKind.INTERFACE: DeclarationFamily.INTERFACE,
            SourceSymbolKind.ANNOTATION: DeclarationFamily.INTERFACE,
            SourceSymbolKind.TRAIT: DeclarationFamily.TYPE,
            SourceSymbolKind.MODULE: DeclarationFamily.TYPE,
            SourceSymbolKind.TYPE_ALIAS: DeclarationFamily.TYPE,
            SourceSymbolKind.FUNCTION: DeclarationFamily.FUNCTION,
            SourceSymbolKind.CALLABLE: DeclarationFamily.CALLABLE,
            SourceSymbolKind.VALUE_CALLABLE: DeclarationFamily.VALUE,
            SourceSymbolKind.VALUE_CLASS: DeclarationFamily.VALUE,
            SourceSymbolKind.VALUE_LITERAL: DeclarationFamily.VALUE,
            SourceSymbolKind.VALUE_OBJECT: DeclarationFamily.VALUE,
            SourceSymbolKind.VALUE_UNKNOWN: DeclarationFamily.VALUE,
        }[kind]
