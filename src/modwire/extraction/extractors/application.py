from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ...shared.code.application import CodeApplication
from ...shared.code.domain import PackageVersion
from ...shared.code.models.code_map import CodeMap
from ...shared.code.models.code_map_producer import CodeMapProducer
from ...shared.code.models.queryable_code_map import QueryableCodeMap
from ...shared.code.models.source_extraction import SourceExtraction
from ..dependency.application import DependencyApplication
from .domain import SourceExtractor, SourceParser
from .models.extraction_request import ExtractionRequest


@injectable
@dataclass(frozen=True)
class ExtractorsApplication:
    extractors: Mapping[Hashable, SourceExtractor]
    dependency: DependencyApplication
    code: CodeApplication
    parsers: Mapping[Hashable, SourceParser]
    version: PackageVersion

    def supported_languages(self) -> tuple[str, ...]:
        return tuple(
            item.runtime.descriptor.language
            for item in sorted(self.extractors.values(), key=lambda item: item.runtime.order)
        )

    def request(self, language: str, root: str) -> ExtractionRequest:
        if language not in self.extractors:
            raise ValueError(f"Language is not supported: {language}")
        extractor = self.extractors[language]
        return ExtractionRequest(root=root, runtime=extractor.runtime, batch_config=extractor.batch_config)

    def generate_map(self, request: ExtractionRequest, extraction: SourceExtraction) -> CodeMap:
        language = request.runtime.descriptor.language
        if language not in self.extractors:
            raise ValueError(f"Language is not supported: {language}")
        extractor = self.extractors[language]
        identities = extractor.module_identities(extraction.files)
        files = self.dependency.resolve(extraction.files, identities)
        resolved = extraction.model_copy(update={"files": files})
        producer = CodeMapProducer(
            modwire_version=self.version.version(),
            extractor=request.runtime.descriptor,
            capabilities=request.runtime.capabilities,
        )
        return CodeMap(
            language=language,
            producer=producer,
            extraction=resolved,
            dependency_graph=self.dependency.build(files),
        )

    def generate_queryable_map(self, request: ExtractionRequest, extraction: SourceExtraction) -> QueryableCodeMap:
        return self.code.queryable(self.generate_map(request, extraction))

    def parse_source(self, language: str, content: str, path: str, root: str, source_id: str) -> dict[str, object]:
        if language not in self.parsers:
            raise ValueError(f"In-process parsing is not supported for language: {language}")
        return self.parsers[language].extract(content, path, root, source_id)
