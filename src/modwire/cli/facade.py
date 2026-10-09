from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..architecture.config.models.architecture_config import ArchitectureConfig
from ..architecture.facade import ArchitectureFacade
from ..architecture.report.models.report_node import ReportNode
from ..extraction.extractors.models.extraction_request import ExtractionRequest
from ..extraction.extractors.models.parsed_source_batch import ParsedSourceBatch
from ..extraction.facade import ExtractionFacade
from ..shared.code.models.code_map import CodeMap
from ..shared.code.models.queryable_code_map import QueryableCodeMap
from ..shared.code.models.scan_policy import ScanPolicy
from ..shared.code.models.source_extraction import SourceExtraction
from ..shared.code.models.source_manifest_identity import SourceManifestIdentity
from .cache.application import CacheApplication
from .cache.models.cache_options import CacheOptions
from .cache.models.cache_plan import CachePlan
from .cache.models.cached_result import CachedResult
from .documentation.application import DocumentationApplication
from .initialization.application import InitializationApplication
from .pipeline.application import PipelineApplication
from .pipeline.models.command_name import CommandName
from .pipeline.models.command_request import CommandRequest
from .pipeline.models.extractor_command_input import ExtractorCommandInput


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

    def source_manifest_identity(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceManifestIdentity:
        return self.pipeline.source_manifest_identity(request, policy)

    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        return self.pipeline.has_source_files(request, policy)

    def prepare_cache(self, request: ExtractionRequest, policy: ScanPolicy) -> CachePlan:
        return self.cache.prepare(request, policy)

    def cached_sources(
        self, request: ExtractionRequest, plan: CachePlan, options: CacheOptions
    ) -> CachedResult[SourceExtraction]:
        return self.cache.sources(request, plan, options)

    def maintain_source_set(self, plan: CachePlan, options: CacheOptions) -> bool:
        return self.cache.maintain_source_set(plan, options)

    def cached_code_map(self, plan: CachePlan, options: CacheOptions) -> CachedResult[CodeMap | None]:
        return self.cache.code_map(plan, options)

    def store_code_map(self, plan: CachePlan, code_map: CodeMap, options: CacheOptions) -> None:
        self.cache.store_code_map(plan, code_map, options)

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

    def maintain_cache(self, options: CacheOptions) -> bool:
        return self.cache.maintain(options)

    def render(self, reports: tuple[ReportNode, ...], summary: bool) -> int:
        return self.pipeline.run(reports, summary=summary)

    def read_sources(self, language: str) -> ExtractorCommandInput | None:
        return self.pipeline.read_sources(language)

    def write_sources(self, document: str) -> int:
        return self.pipeline.write_sources(document)

    def generate_documentation(self, readme: str, public_interfaces: tuple[type[object], ...], check: bool) -> int:
        return self.documentation.generate(Path(readme), public_interfaces, check)

    def run_extractor(self, language: str) -> int:
        request = self.read_sources(language)
        if request is None:
            return 1
        if request.batch:
            return self.write_sources(
                ParsedSourceBatch(
                    sources={
                        source.source_id: self.extraction.parse_source(
                            language, source.content, str(source.path), str(source.root), source.source_id
                        )
                        for source in request.sources
                    }
                ).document()
            )
        source = request.sources[0]
        return self.write_sources(
            self.extraction.parse_source(
                language, source.content, str(source.path), str(source.root), source.source_id
            ).model_dump_json()
        )

    def run(self, argv: Sequence[str]) -> int:
        request = self.parse(argv)
        if request.command is CommandName.INIT:
            return self.initialize(self.working_directory(), str(request.dot_dir), request.force)
        cache_options = CacheOptions(
            directory=str(request.cache_directory),
            namespace=request.cache_namespace,
            max_bytes=request.cache_max_bytes,
        )
        if request.command is CommandName.CACHE_CLEAR:
            self.clear_cache(cache_options)
            return 0
        config = self.load_configuration(str(request.dot_dir))
        extraction_request = self.extraction.request(request.language, str(request.architecture_root))
        policy = ScanPolicy(excluded_patterns=config.excluded_patterns)
        if request.no_cache:
            extraction = self.extract(extraction_request, policy)
            code_map = self.extraction.generate_queryable_map(extraction_request, extraction)
            return self.render(self.architecture.analyze(code_map, config), request.summary)
        plan = self.prepare_cache(extraction_request, policy)
        cached_code_map = self.cached_code_map(plan, cache_options).value
        if cached_code_map is None:
            extraction = self.cached_sources(extraction_request, plan, cache_options).value
            self.maintain_source_set(plan, cache_options)
            cached_code_map = self.extraction.generate_map(extraction_request, extraction)
            self.store_code_map(plan, cached_code_map, cache_options)
        code_map = QueryableCodeMap(code_map=cached_code_map)
        reports = self.cached_reports(cached_code_map, config, cache_options).value
        if reports is None:
            reports = self.architecture.analyze(code_map, config)
            self.store_reports(cached_code_map, config, reports, cache_options)
        self.maintain_cache(cache_options)
        return self.render(reports, request.summary)
