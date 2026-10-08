from dataclasses import dataclass

from pydantic import TypeAdapter
from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.identity import FileId
from .output_reader import ExtractorBatchOutputReader


@injectable(as_type=ExtractorBatchOutputReader, qualifier="json")
@dataclass(frozen=True)
class JsonBatchOutputReader(ExtractorBatchOutputReader):
    def read(self, document: str) -> dict[FileId, ParsedSourceFile]:
        return TypeAdapter(dict[FileId, ParsedSourceFile]).validate_json(document)
