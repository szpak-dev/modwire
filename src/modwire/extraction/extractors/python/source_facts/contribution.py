from pydantic import Field

from .....shared.code.models.source_abstract_class import SourceAbstractClass
from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.source_callable import SourceCallable
from .....shared.code.models.source_class import SourceClass
from .....shared.code.models.source_class_property import SourceClassProperty
from .....shared.code.models.source_export import SourceExport
from .....shared.code.models.source_function import SourceFunction
from .....shared.code.models.source_import import SourceImport
from .....shared.code.models.source_inheritance import SourceInheritance
from .....shared.code.models.source_interface import SourceInterface
from .....shared.code.models.source_type import SourceType
from .....shared.code.models.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel
from ...models.parsed_source_file import ParsedSourceFile


class PythonSourceFactContribution(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    classes: tuple[SourceClass, ...] = Field(default_factory=tuple)
    interfaces: tuple[SourceInterface, ...] = Field(default_factory=tuple)
    types: tuple[SourceType, ...] = Field(default_factory=tuple)
    abstract_classes: tuple[SourceAbstractClass, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callables: tuple[SourceCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    inheritance: tuple[SourceInheritance, ...] = Field(default_factory=tuple)
    properties: dict[str, tuple[SourceClassProperty, ...]] = Field(default_factory=dict)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0

    def combine(self, contribution: "PythonSourceFactContribution") -> "PythonSourceFactContribution":
        properties = dict(self.properties)
        for name, items in contribution.properties.items():
            current = properties[name] if name in properties else ()
            properties[name] = (*current, *items)
        return PythonSourceFactContribution(
            imports=(*self.imports, *contribution.imports),
            exports=(*self.exports, *contribution.exports),
            classes=(*self.classes, *contribution.classes),
            interfaces=(*self.interfaces, *contribution.interfaces),
            types=(*self.types, *contribution.types),
            abstract_classes=(*self.abstract_classes, *contribution.abstract_classes),
            functions=(*self.functions, *contribution.functions),
            values=(*self.values, *contribution.values),
            callables=(*self.callables, *contribution.callables),
            calls=(*self.calls, *contribution.calls),
            inheritance=(*self.inheritance, *contribution.inheritance),
            properties=properties,
            line_count=self.line_count + contribution.line_count,
            code_line_count=self.code_line_count + contribution.code_line_count,
            public_symbol_count=self.public_symbol_count + contribution.public_symbol_count,
        )

    def parsed(self) -> ParsedSourceFile:
        return ParsedSourceFile(
            imports=list(self.imports),
            exports=list(self.exports),
            classes=[
                item.model_copy(
                    update={
                        "properties": (
                            list(self.properties[str(item.declaration_id.ordinal)])
                            if str(item.declaration_id.ordinal) in self.properties
                            else []
                        )
                    }
                )
                for item in self.classes
            ],
            interfaces=list(self.interfaces),
            types=list(self.types),
            abstract_classes=[
                item.model_copy(
                    update={
                        "properties": (
                            list(self.properties[str(item.declaration_id.ordinal)])
                            if str(item.declaration_id.ordinal) in self.properties
                            else []
                        )
                    }
                )
                for item in self.abstract_classes
            ],
            functions=list(self.functions),
            values=list(self.values),
            callables=list(self.callables),
            calls=list(self.calls),
            inheritance=list(self.inheritance),
            line_count=self.line_count,
            code_line_count=self.code_line_count,
            public_symbol_count=self.public_symbol_count,
        )
