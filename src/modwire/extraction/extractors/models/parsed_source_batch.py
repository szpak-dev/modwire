from pydantic import TypeAdapter

from ....shared.code.models.identity import FileId
from ....shared.values.models.value_model import ValueModel
from .parsed_source_file import ParsedSourceFile


class ParsedSourceBatch(ValueModel):
    sources: dict[FileId, ParsedSourceFile]

    def document(self) -> str:
        adapter = TypeAdapter(dict[FileId, ParsedSourceFile])
        return adapter.dump_json(self.sources).decode()
