from dataclasses import dataclass

from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.identity import FileId, ImportIdentity
from ....shared.code.models.source_file import SourceFile


@injectable
@dataclass(frozen=True)
class SourceFileFactory:
    def create(self, file_id: FileId, import_identity: ImportIdentity, parsed: ParsedSourceFile) -> SourceFile:
        return SourceFile(
            file_id=file_id,
            import_identity=import_identity,
            imports=parsed.imports,
            exports=parsed.exports,
            namespaces=tuple(parsed.namespaces),
            declarations=tuple(parsed.declarations),
            functions=parsed.functions,
            values=parsed.values,
            callables=parsed.callables,
            calls=parsed.calls,
            declaration_relations=tuple(parsed.declaration_relations),
            line_count=parsed.line_count,
            code_line_count=parsed.code_line_count,
            public_symbol_count=parsed.public_symbol_count,
        )
