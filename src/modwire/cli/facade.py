from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..architecture.config.models.architecture_config import ArchitectureConfig
from ..architecture.facade import ArchitectureFacade
from ..architecture.report.models.report_node import ReportNode
from ..extraction.extractors.models.extraction_request import ExtractionRequest
from ..extraction.facade import ExtractionFacade
from ..shared.code.models.code_map import CodeMap
from ..shared.code.models.queryable_code_map import QueryableCodeMap
from ..shared.code.models.source_extraction import SourceExtraction
from .cache.application import CacheApplication
from .cache.models.cache_options import CacheOptions
from .cache.models.cached_result import CachedResult
from .cache.models.extraction_snapshot import ExtractionSnapshot
from .documentation.application import DocumentationApplication
from .initialization.application import InitializationApplication
from .pipeline.application import PipelineApplication
from .pipeline.models.command_request import CommandRequest
from .pipeline.models.extractor_command_input import ExtractorCommandInput
from .pipeline.models.scan_policy import ScanPolicy


@injectable
@dataclass(frozen=True)
class CliFacade:
    architecture: ArchitectureFacade
    extraction: ExtractionFacade
    initialization: InitializationApplication
    pipeline: PipelineApplication
    cache: CacheApplication
    documentation: DocumentationApplication

    def working_directory(self) -> str:
        return str(Path.cwd())

    def parse(self, argv: Sequence[str]) -> CommandRequest:
        return self.pipeline.parse(argv)

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        return self.pipeline.load_configuration(Path(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        return self.initialization.initialize(Path(root), Path(dot_dir), force)

    def extract(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceExtraction:
        return self.pipeline.extract(request, policy)

    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        return self.pipeline.has_source_files(request, policy)

    def extract_cached(
        self, request: ExtractionRequest, policy: ScanPolicy, options: CacheOptions
    ) -> CachedResult[ExtractionSnapshot]:
        return self.cache.extract_cached(request, policy, options)

    def cached_code_map(self, snapshot: ExtractionSnapshot, options: CacheOptions) -> CachedResult[CodeMap | None]:
        return self.cache.code_map(snapshot, options)

    def store_code_map(self, snapshot: ExtractionSnapshot, code_map: CodeMap, options: CacheOptions) -> None:
        self.cache.store_code_map(snapshot, code_map, options)

    def cached_reports(
        self, code_map: CodeMap, config: ArchitectureConfig, options: CacheOptions
    ) -> CachedResult[tuple[ReportNode, ...] | None]:
        return self.cache.reports(code_map, config, options)

    def store_reports(
        self,
        code_map: CodeMap,
        config: ArchitectureConfig,
        reports: tuple[ReportNode, ...],
        options: CacheOptions,
    ) -> None:
        self.cache.store_reports(code_map, config, reports, options)

    def clear_cache(self, options: CacheOptions) -> None:
        self.cache.clear(options)

    def render(self, reports: tuple[ReportNode, ...], summary: bool) -> int:
        return self.pipeline.run(reports, summary=summary)

    def read_sources(self, language: str) -> ExtractorCommandInput | None:
        return self.pipeline.read_sources(language)

    def write_sources(self, result: dict[str, object]) -> int:
        return self.pipeline.write_sources(result)

    def generate_documentation(self, readme: str, public_interfaces: tuple[type[object], ...], check: bool) -> int:
        return self.documentation.generate(Path(readme), public_interfaces, check)

    def run_extractor(self, language: str) -> int:
        request = self.read_sources(language)
        if request is None:
            return 1
        if request.batch:
            result: dict[str, object] = {
                source.source_id: self.extraction.parse_source(
                    language, source.content, str(source.path), str(source.root), source.source_id
                )
                for source in request.sources
            }
            return self.write_sources(result)
        source = request.sources[0]
        return self.write_sources(
            self.extraction.parse_source(language, source.content, str(source.path), str(source.root), source.source_id)
        )

    def run(self, argv: Sequence[str]) -> int:
        request = self.parse(argv)
        if request.command == "init":
            return self.initialize(self.working_directory(), str(request.dot_dir), request.force)
        cache_options = CacheOptions(
            directory=str(request.cache_directory),
            namespace=request.cache_namespace,
            max_bytes=request.cache_max_bytes,
        )
        if request.command == "cache-clear":
            self.clear_cache(cache_options)
            return 0
        config = self.load_configuration(str(request.dot_dir))
        extraction_request = self.extraction.request(request.language, str(request.architecture_root))
        policy = ScanPolicy(excluded_patterns=config.excluded_patterns)
        if request.no_cache:
            extraction = self.extract(extraction_request, policy)
            code_map = self.extraction.generate_queryable_map(request.language, extraction)
            return self.render(self.architecture.analyze(code_map, config), request.summary)
        snapshot = self.extract_cached(extraction_request, policy, cache_options).value
        cached_code_map = self.cached_code_map(snapshot, cache_options).value
        if cached_code_map is None:
            cached_code_map = self.extraction.generate_map(request.language, snapshot.extraction)
            self.store_code_map(snapshot, cached_code_map, cache_options)
        code_map = QueryableCodeMap(code_map=cached_code_map)
        reports = self.cached_reports(cached_code_map, config, cache_options).value
        if reports is None:
            reports = self.architecture.analyze(code_map, config)
            self.store_reports(cached_code_map, config, reports, cache_options)
        return self.render(reports, request.summary)
