from pydantic import Field

from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.source_callable import SourceCallable
from .....shared.code.models.source_class_property import SourceClassProperty
from .....shared.code.models.source_declaration import SourceDeclaration
from .....shared.code.models.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.source_export import SourceExport
from .....shared.code.models.source_function import SourceFunction
from .....shared.code.models.source_import import SourceImport
from .....shared.code.models.source_namespace import SourceNamespace
from .....shared.code.models.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel
from .contribution import PythonSemanticContribution


class PythonSemanticCatalog(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callables: tuple[SourceCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = Field(default_factory=tuple)
    properties: dict[str, tuple[SourceClassProperty, ...]] = Field(default_factory=dict)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0

    def combine(self, contribution: PythonSemanticContribution) -> "PythonSemanticCatalog":
        properties = dict(self.properties)
        for name, items in contribution.properties.items():
            current = properties[name] if name in properties else ()
            properties[name] = (*current, *items)
        return PythonSemanticCatalog(
            imports=(*self.imports, *contribution.imports),
            exports=(*self.exports, *contribution.exports),
            namespaces=(*self.namespaces, *contribution.namespaces),
            declarations=(*self.declarations, *contribution.declarations),
            functions=(*self.functions, *contribution.functions),
            values=(*self.values, *contribution.values),
            callables=(*self.callables, *contribution.callables),
            calls=(*self.calls, *contribution.calls),
            declaration_relations=(*self.declaration_relations, *contribution.declaration_relations),
            properties=properties,
            line_count=self.line_count + contribution.line_count,
            code_line_count=self.code_line_count + contribution.code_line_count,
            public_symbol_count=self.public_symbol_count + contribution.public_symbol_count,
        )
