from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .declaration_family import DeclarationFamily
from .identity import FileId, ImportIdentity
from .source_call import SourceCall
from .source_callable import SourceCallable
from .source_declaration import SourceDeclaration
from .source_declaration_relation import SourceDeclarationRelation
from .source_export import SourceExport
from .source_function import SourceFunction
from .source_import import SourceImport
from .source_namespace import SourceNamespace
from .source_symbol_kind import SourceSymbolKind
from .source_value import SourceValue


class SourceFile(ValueModel):
    file_id: FileId
    import_identity: ImportIdentity
    imports: list[SourceImport]
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: list[SourceFunction]
    values: list[SourceValue] = Field(default_factory=list[SourceValue])
    callables: list[SourceCallable] = Field(default_factory=list[SourceCallable])
    calls: list[SourceCall] = Field(default_factory=list[SourceCall])
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
                raise ValueError("Source declaration identities must be unique within each fact collection.")
            if any(item.declaration_id.source_id != self.file_id for item in declarations):
                raise ValueError("Source declaration identities must reference their owning source file.")
            if family is not None and any(item.declaration_id.family is not family for item in declarations):
                raise ValueError("Source declaration identity family must match its fact collection.")
            if any(item.declaration_id.qualified_name != item.name for item in declarations):
                raise ValueError("Source declaration identity must match its declaration name.")
        if any(self.declaration_family(item.kind) is not item.declaration_id.family for item in self.declarations):
            raise ValueError("Source declaration kind must match its identity family.")
        callable_identities = tuple(item.declaration_id.canonical() for item in self.callables)
        if len(callable_identities) != len(set(callable_identities)):
            raise ValueError("Source callable declaration identities must be unique.")
        if any(item.declaration_id.source_id != self.file_id for item in self.callables):
            raise ValueError("Source callable declaration identities must reference their owning source file.")
        declaration_identities = {item.declaration_id.canonical() for item in self.declarations}
        if any(
            relation.source_declaration_id.canonical() not in declaration_identities
            for relation in self.declaration_relations
        ):
            raise ValueError("Source declaration relations must reference an extracted declaration.")
        return self

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
