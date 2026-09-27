from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .declaration_family import DeclarationFamily
from .identity import FileId, ModuleId
from .source_abstract_class import SourceAbstractClass
from .source_call import SourceCall
from .source_callable import SourceCallable
from .source_class import SourceClass
from .source_export import SourceExport
from .source_function import SourceFunction
from .source_import import SourceImport
from .source_inheritance import SourceInheritance
from .source_interface import SourceInterface
from .source_type import SourceType
from .source_value import SourceValue


class SourceFile(ValueModel):
    file_id: FileId
    module_id: ModuleId
    imports: list[SourceImport]
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    classes: list[SourceClass]
    interfaces: list[SourceInterface] = Field(default_factory=list[SourceInterface])
    types: list[SourceType] = Field(default_factory=list[SourceType])
    abstract_classes: list[SourceAbstractClass] = Field(default_factory=list[SourceAbstractClass])
    functions: list[SourceFunction]
    values: list[SourceValue] = Field(default_factory=list[SourceValue])
    callables: list[SourceCallable] = Field(default_factory=list[SourceCallable])
    calls: list[SourceCall] = Field(default_factory=list[SourceCall])
    inheritance: tuple[SourceInheritance, ...] = Field(default_factory=tuple)
    line_count: int
    code_line_count: int
    public_symbol_count: int

    @model_validator(mode="after")
    def validate_declaration_identities(self) -> Self:
        declarations_by_family = (
            (self.classes, DeclarationFamily.CLASS),
            (self.abstract_classes, DeclarationFamily.ABSTRACT_CLASS),
            (self.interfaces, DeclarationFamily.INTERFACE),
            (self.types, DeclarationFamily.TYPE),
            (self.functions, DeclarationFamily.FUNCTION),
            (self.values, DeclarationFamily.VALUE),
        )
        for declarations, family in declarations_by_family:
            identities = tuple(item.declaration_id.canonical() for item in declarations)
            if len(identities) != len(set(identities)):
                raise ValueError("Source declaration identities must be unique within each fact collection.")
            if any(item.declaration_id.source_id != self.file_id for item in declarations):
                raise ValueError("Source declaration identities must reference their owning source file.")
            if any(item.declaration_id.family is not family for item in declarations):
                raise ValueError("Source declaration identity family must match its fact collection.")
            if any(item.declaration_id.qualified_name != item.name for item in declarations):
                raise ValueError("Source declaration identity must match its declaration name.")
        callable_identities = tuple(item.declaration_id.canonical() for item in self.callables)
        if len(callable_identities) != len(set(callable_identities)):
            raise ValueError("Source callable declaration identities must be unique.")
        if any(item.declaration_id.source_id != self.file_id for item in self.callables):
            raise ValueError("Source callable declaration identities must reference their owning source file.")
        type_identities = {
            item.declaration_id.canonical()
            for declarations in (self.classes, self.abstract_classes, self.interfaces, self.types)
            for item in declarations
        }
        if any(relation.source_declaration_id.canonical() not in type_identities for relation in self.inheritance):
            raise ValueError("Source inheritance must reference an extracted type declaration.")
        return self
