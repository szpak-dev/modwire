from pydantic import Field

from .....shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from .....shared.code.models.callables.source_callable_value import SourceCallableValue
from .....shared.code.models.callables.source_function import SourceFunction
from .....shared.code.models.declarations.source_declaration import SourceDeclaration
from .....shared.code.models.declarations.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.declarations.source_namespace import SourceNamespace
from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.sources.source_export import SourceExport
from .....shared.code.models.sources.source_import import SourceImport
from .....shared.code.models.values.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel
from ...models.parsed_source_file import ParsedSourceFile


class PythonSourceFactContribution(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callable_values: tuple[SourceCallableValue, ...] = Field(default_factory=tuple)
    anonymous_callables: tuple[SourceAnonymousCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = Field(default_factory=tuple)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0

    def combine(self, contribution: "PythonSourceFactContribution") -> "PythonSourceFactContribution":
        return PythonSourceFactContribution(
            imports=(*self.imports, *contribution.imports),
            exports=(*self.exports, *contribution.exports),
            namespaces=(*self.namespaces, *contribution.namespaces),
            declarations=(*self.declarations, *contribution.declarations),
            functions=(*self.functions, *contribution.functions),
            values=(*self.values, *contribution.values),
            callable_values=(*self.callable_values, *contribution.callable_values),
            anonymous_callables=(*self.anonymous_callables, *contribution.anonymous_callables),
            calls=(*self.calls, *contribution.calls),
            declaration_relations=(*self.declaration_relations, *contribution.declaration_relations),
            line_count=self.line_count + contribution.line_count,
            code_line_count=self.code_line_count + contribution.code_line_count,
            public_symbol_count=self.public_symbol_count + contribution.public_symbol_count,
        )

    def parsed(self) -> ParsedSourceFile:
        return ParsedSourceFile(
            imports=list(self.imports),
            exports=list(self.exports),
            namespaces=list(self.namespaces),
            declarations=list(self.declarations),
            functions=list(self.functions),
            values=list(self.values),
            callable_values=list(self.callable_values),
            anonymous_callables=list(self.anonymous_callables),
            calls=list(self.calls),
            declaration_relations=list(self.declaration_relations),
            line_count=self.line_count,
            code_line_count=self.code_line_count,
            public_symbol_count=self.public_symbol_count,
        )
