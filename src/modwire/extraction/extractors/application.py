from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from modwire.extraction.dependency.application import DependencyApplication
from modwire.shared.code.application import CodeApplication
from modwire.shared.code.models.code_map import CodeMap
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap
from modwire.shared.code.models.source_extraction import SourceExtraction

from .domain import PythonParser, SourceExtractor
from .models.extraction_request import ExtractionRequest


@injectable
@dataclass(frozen=True)
class ExtractorsApplication:
    extractors: Mapping[Hashable, SourceExtractor]
    dependency: DependencyApplication
    code: CodeApplication
    parser: PythonParser

    def supported_languages(self) -> tuple[str, ...]:
        return tuple(
            item.runtime.language for item in sorted(self.extractors.values(), key=lambda item: item.runtime.order)
        )

    def request(self, language: str, root: Path) -> ExtractionRequest:
        if language not in self.extractors:
            raise ValueError(f"Language is not supported: {language}")
        extractor = self.extractors[language]
        return ExtractionRequest(root=root, runtime=extractor.runtime, batch_config=extractor.batch_config)

    def generate_map(self, language: str, extraction: SourceExtraction) -> CodeMap:
        files = self.dependency.resolve(extraction.files)
        resolved = extraction.model_copy(update={"files": files})
        return CodeMap(language=language, extraction=resolved, dependency_graph=self.dependency.build(files))

    def generate_queryable_map(self, language: str, extraction: SourceExtraction) -> QueryableCodeMap:
        return self.code.queryable(self.generate_map(language, extraction))

    def parse_python(self, content: str, path: Path, root: Path, source_id: str) -> dict[str, object]:
        return self.parser.extract(content, path, root, source_id)
