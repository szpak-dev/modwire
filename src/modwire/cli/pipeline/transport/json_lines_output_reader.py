from dataclasses import dataclass

from pydantic import TypeAdapter
from wireup import injectable

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.identity import FileId
from .output_reader import ExtractorBatchOutputReader


@injectable(as_type=ExtractorBatchOutputReader, qualifier="jsonl")
@dataclass(frozen=True)
class JsonLinesBatchOutputReader(ExtractorBatchOutputReader):
    def read(self, document: str) -> dict[FileId, ParsedSourceFile]:
        adapter = TypeAdapter(tuple[FileId, ParsedSourceFile])
        return dict(adapter.validate_json(line) for line in document.splitlines())
