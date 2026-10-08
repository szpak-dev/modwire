from abc import ABC, abstractmethod

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.identity import FileId


class ExtractorBatchOutputReader(ABC):
    @abstractmethod
    def read(self, document: str) -> dict[FileId, ParsedSourceFile]:
        raise NotImplementedError
