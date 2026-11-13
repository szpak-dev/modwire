from dataclasses import dataclass

from wireup import injectable

from ...models.parsed_source_file import ParsedSourceFile
from ..semantics.catalog import PythonSemanticCatalog


@injectable
@dataclass(frozen=True)
class PythonSourceAssembler:
    def assemble(self, catalog: PythonSemanticCatalog) -> ParsedSourceFile:
        return ParsedSourceFile(
            imports=list(catalog.imports),
            exports=list(catalog.exports),
            namespaces=list(catalog.namespaces),
            declarations=list(catalog.declarations),
            functions=list(catalog.functions),
            values=list(catalog.values),
            callable_values=list(catalog.callable_values),
            anonymous_callables=list(catalog.anonymous_callables),
            calls=list(catalog.calls),
            declaration_relations=list(catalog.declaration_relations),
            line_count=catalog.line_count,
            code_line_count=catalog.code_line_count,
            public_symbol_count=catalog.public_symbol_count,
        )
