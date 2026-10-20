from abc import ABC, abstractmethod

from ...shared.code.models.identity import FileId, ImportIdentity
from ...shared.code.models.source_file import SourceFile
from .models.batch_config import BatchConfig
from .models.extractor_runtime import ExtractorRuntime
from .models.parsed_source_file import ParsedSourceFile


class SourceParser(ABC):
    @abstractmethod
    def extract(self, content: str, path: str, sources_root: str, source_id: FileId) -> ParsedSourceFile:
        raise NotImplementedError


class SourceExtractor(ABC):
    @property
    @abstractmethod
    def runtime(self) -> ExtractorRuntime:
        raise NotImplementedError

    @property
    @abstractmethod
    def batch_config(self) -> BatchConfig:
        raise NotImplementedError

    @abstractmethod
    def import_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        raise NotImplementedError
