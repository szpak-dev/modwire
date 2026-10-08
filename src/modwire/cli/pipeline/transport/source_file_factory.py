from dataclasses import dataclass

from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.identity import FileId, ModuleId
from ....shared.code.models.source_file import SourceFile


@injectable
@dataclass(frozen=True)
class SourceFileFactory:
    def create(self, file_id: FileId, module_id: ModuleId, parsed: ParsedSourceFile) -> SourceFile:
        return SourceFile(
            file_id=file_id,
            module_id=module_id,
            imports=parsed.imports,
            exports=parsed.exports,
            classes=parsed.classes,
            interfaces=parsed.interfaces,
            types=parsed.types,
            abstract_classes=parsed.abstract_classes,
            functions=parsed.functions,
            values=parsed.values,
            callables=parsed.callables,
            calls=parsed.calls,
            inheritance=tuple(parsed.inheritance),
            line_count=parsed.line_count,
            code_line_count=parsed.code_line_count,
            public_symbol_count=parsed.public_symbol_count,
        )
