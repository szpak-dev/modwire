from pydantic import ConfigDict, TypeAdapter
from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.code.models.immutable_code_value import ImmutableCodeValue
from ....shared.code.models.sources.identity import FileId
from ....shared.values.models.value_reuse import ValueReuse
from .indexed_source_record import IndexedSourceRecord


@injectable
class ExtractorBatchOutputReader:
    records: TypeAdapter[tuple[FileId, ParsedSourceFile]]
    indexed_records: TypeAdapter[IndexedSourceRecord]

    def __init__(self) -> None:
        self.records = TypeAdapter(tuple[FileId, ParsedSourceFile], config=ConfigDict(cache_strings="keys"))
        self.indexed_records = TypeAdapter(IndexedSourceRecord)
        self.indexed_records.rebuild()

    def read(
        self, document: bytes, reuse: ValueReuse[ImmutableCodeValue | DeclarationIdentity]
    ) -> tuple[FileId, ParsedSourceFile]:
        try:
            if reuse.indexed:
                record = self.indexed_records.validate_json(document, context=reuse)
                return record.source_id, record.facts
            return self.records.validate_json(document, context=reuse)
        finally:
            reuse.references.clear()
