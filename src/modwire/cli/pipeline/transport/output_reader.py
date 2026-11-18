from pydantic import TypeAdapter
from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.immutable_code_value import ImmutableCodeValue
from ....shared.code.models.sources.identity import FileId
from ....shared.values.models.value_reuse import ValueReuse


@injectable
class ExtractorBatchOutputReader:
    records: TypeAdapter[tuple[FileId, ParsedSourceFile]]

    def __init__(self) -> None:
        self.records = TypeAdapter(tuple[FileId, ParsedSourceFile])

    def read(self, document: bytes, reuse: ValueReuse[ImmutableCodeValue]) -> tuple[FileId, ParsedSourceFile]:
        return self.records.validate_json(document, context=reuse)
