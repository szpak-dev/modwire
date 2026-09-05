from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from modwire.extraction.extractors.application import ExtractorsApplication
from modwire.extraction.extractors.models.extraction_request import ExtractionRequest
from modwire.shared.code.models.code_map import CodeMap
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap
from modwire.shared.code.models.source_extraction import SourceExtraction


@injectable
@dataclass(frozen=True)
class ExtractionFacade:
    """Parse supplied source and assemble dependency maps without filesystem access."""

    extractors: ExtractorsApplication

    def supported_languages(self) -> tuple[str, ...]:
        return self.extractors.supported_languages()

    def request(self, language: str, root: Path) -> ExtractionRequest:
        return self.extractors.request(language, root)

    def generate_map(self, language: str, extraction: SourceExtraction) -> CodeMap:
        return self.extractors.generate_map(language, extraction)

    def generate_queryable_map(self, language: str, extraction: SourceExtraction) -> QueryableCodeMap:
        return self.extractors.generate_queryable_map(language, extraction)

    def parse_python(self, content: str, path: Path, root: Path, source_id: str) -> dict[str, object]:
        return self.extractors.parse_python(content, path, root, source_id)
