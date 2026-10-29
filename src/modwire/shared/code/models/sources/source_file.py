from typing import Self

from pydantic import Field, model_validator

from ....values.models.value_model import ValueModel
from ..callables.source_anonymous_callable import SourceAnonymousCallable
from ..callables.source_callable import SourceCallable
from ..callables.source_callable_value import SourceCallableValue
from ..callables.source_function import SourceFunction
from ..code_validation_error import CodeValidationError
from ..code_violation import CodeViolation
from ..declaration_family import DeclarationFamily
from ..declarations.source_declaration import SourceDeclaration
from ..declarations.source_declaration_relation import SourceDeclarationRelation
from ..declarations.source_namespace import SourceNamespace
from ..source_call import SourceCall
from ..source_symbol_kind import SourceSymbolKind
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
    line_count: int
    code_line_count: int
    public_symbol_count: int

    @model_validator(mode="after")
    def validate_declaration_identities(self) -> Self:
        declarations_by_family = (
            (self.declarations, None),
            (self.functions, DeclarationFamily.FUNCTION),
            (self.values, DeclarationFamily.VALUE),
        )
        for declarations, family in declarations_by_family:
            identities = tuple(item.declaration_id.canonical() for item in declarations)
            if len(identities) != len(set(identities)):
                raise CodeValidationError(CodeViolation.DUPLICATE_DECLARATION_IDENTITY, str(self.file_id))
            if any(item.declaration_id.source_id != self.file_id for item in declarations):
                raise CodeValidationError(CodeViolation.FOREIGN_DECLARATION_IDENTITY, str(self.file_id))
            if family is not None and any(item.declaration_id.family is not family for item in declarations):
                raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_FAMILY, str(self.file_id))
            if any(item.declaration_id.qualified_name != item.name for item in declarations):
                raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_NAME, str(self.file_id))
        if any(self.declaration_family(item.kind) is not item.declaration_id.family for item in self.declarations):
            raise CodeValidationError(CodeViolation.INCONSISTENT_DECLARATION_KIND, str(self.file_id))
        callables = self.canonical_callables()
        callable_identities = tuple(item.declaration_id.canonical() for item in callables)
        if len(callable_identities) != len(set(callable_identities)):
            raise CodeValidationError(CodeViolation.DUPLICATE_CALLABLE_IDENTITY, str(self.file_id))
        if any(item.declaration_id.source_id != self.file_id for item in callables):
            raise CodeValidationError(CodeViolation.FOREIGN_CALLABLE_IDENTITY, str(self.file_id))
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
        callables = (
            *self.functions,
            *(method for declaration in self.declarations for method in declaration.methods),
            *(method for declaration in self.declarations for method in declaration.abstract_methods),
            *self.callable_values,
            *self.anonymous_callables,
        )
        return tuple(sorted(callables, key=lambda item: item.declaration_id.ordinal))

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
