from dataclasses import dataclass

from wireup import injectable

from ..shared.code.models.code_map import CodeMap
from ..shared.code.models.identity import FileId
from ..shared.code.models.queryable_code_map import QueryableCodeMap
from ..shared.code.models.source_extraction import SourceExtraction
from .extractors.application import ExtractorsApplication
from .extractors.models.extraction_request import ExtractionRequest
from .extractors.models.parsed_source_file import ParsedSourceFile


@injectable
@dataclass(frozen=True)
class ExtractionFacade:
    extractors: ExtractorsApplication

    def supported_languages(self) -> tuple[str, ...]:
        return self.extractors.supported_languages()

    def request(self, language: str, root: str) -> ExtractionRequest:
        return self.extractors.request(language, root)

    def generate_map(self, request: ExtractionRequest, extraction: SourceExtraction) -> CodeMap:
        return self.extractors.generate_map(request, extraction)

    def generate_queryable_map(self, request: ExtractionRequest, extraction: SourceExtraction) -> QueryableCodeMap:
        return self.extractors.generate_queryable_map(request, extraction)

    def parse_source(self, language: str, content: str, path: str, root: str, source_id: FileId) -> ParsedSourceFile:
        return self.extractors.parse_source(language, content, path, root, source_id)
