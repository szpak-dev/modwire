from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from wireup import create_sync_container

import modwire

from .architecture.config.models.architecture_config import ArchitectureConfig
from .architecture.facade import ArchitectureFacade
from .architecture.report.models.report_catalog import ReportCatalog
from .architecture.report.models.report_node import ReportNode
from .cli.cache.models.cache_options import CacheOptions
from .cli.cache.models.cache_outcome import CacheOutcome, CacheStage
from .cli.cache.models.cached_result import CachedResult
from .cli.facade import CliFacade
from .cli.pipeline.models.scan_policy import ScanPolicy
from .extraction.facade import ExtractionFacade
from .shared.code.models.code_map import CodeMap
from .shared.code.models.queryable_code_map import QueryableCodeMap

__all__ = [
    "CacheOptions",
    "CacheOutcome",
    "CacheStage",
    "CachedResult",
    "CodeMap",
    "ModwireApplication",
    "QueryableCodeMap",
    "ScanPolicy",
]


@dataclass(frozen=True)
class ModwireApplication:
    """Public entry point for source discovery, extraction, architecture analysis, and the Modwire CLI."""

    architecture: ArchitectureFacade
    cli: CliFacade
    extraction: ExtractionFacade

    @classmethod
    def create(cls) -> Self:
        """Create an isolated application with all services resolved through Wireup."""

        container = create_sync_container(injectables=[modwire])
        try:
            return cls(
                architecture=container.get(ArchitectureFacade),
                cli=container.get(CliFacade),
                extraction=container.get(ExtractionFacade),
            )
        finally:
            container.close()

    def configure(self, values: Mapping[str, object]) -> ArchitectureConfig:
        """Validate architecture configuration values."""

        return self.architecture.configure(values)

    def catalog(self) -> ReportCatalog:
        """Return the available architecture reports."""

        return self.architecture.catalog()

    def analyze(self, code_map: QueryableCodeMap, config: ArchitectureConfig) -> tuple[ReportNode, ...]:
        """Analyze a code map with a validated architecture configuration."""

        return self.architecture.analyze(code_map, config)

    def analyze_cached(
        self, code_map: QueryableCodeMap, config: ArchitectureConfig, options: CacheOptions
    ) -> tuple[ReportNode, ...]:
        """Analyze a code map, reusing reports for an exact map and configuration identity."""

        return self.analyze_cached_with_diagnostics(code_map, config, options).value

    def analyze_cached_with_diagnostics(
        self, code_map: QueryableCodeMap, config: ArchitectureConfig, options: CacheOptions
    ) -> CachedResult[tuple[ReportNode, ...]]:
        """Analyze a code map and report the public outcome of report-cache reuse."""

        cached = self.cli.cached_reports(code_map.code_map, config, options)
        if cached.value is not None:
            return CachedResult(value=cached.value, outcomes=cached.outcomes)
        reports = self.architecture.analyze(code_map, config)
        self.cli.store_reports(code_map.code_map, config, reports, options)
        outcome = cached.outcome(CacheStage.REPORTS).model_copy(update={"computed": 1, "stored": 1})
        return CachedResult(value=reports, outcomes=(outcome,))

    def discover(self, root: str, policy: ScanPolicy) -> tuple[str, ...]:
        """Discover supported source languages beneath a root using the caller's scan policy."""

        return tuple(
            language
            for language in self.extraction.supported_languages()
            if self.cli.has_source_files(self.extraction.request(language, str(root)), policy)
        )

    def generate_map(self, language: str, root: str, policy: ScanPolicy) -> CodeMap:
        """Extract one language and return its code map with honest scan metrics.

        ``files_excluded`` counts only source files encountered and excluded directly.
        ``directories_pruned`` counts directories rejected before descent; their
        descendants are deliberately unobserved and are not included in file counts.
        """

        request = self.extraction.request(language, str(root))
        return self.extraction.generate_map(language, self.cli.extract(request, policy))

    def generate_queryable_map(self, language: str, root: str, policy: ScanPolicy) -> QueryableCodeMap:
        """Extract source files and return a queryable code map."""

        return QueryableCodeMap(code_map=self.generate_map(language, root, policy))

    def generate_map_cached(self, language: str, root: str, policy: ScanPolicy, options: CacheOptions) -> CodeMap:
        """Return a code map with content-addressed source and complete-manifest reuse."""

        return self.generate_map_cached_with_diagnostics(language, root, policy, options).value

    def generate_map_cached_with_diagnostics(
        self, language: str, root: str, policy: ScanPolicy, options: CacheOptions
    ) -> CachedResult[CodeMap]:
        """Return a code map and public outcomes for extraction and complete-map reuse."""

        request = self.extraction.request(language, str(root))
        snapshot = self.cli.extract_cached(request, policy, options)
        cached = self.cli.cached_code_map(snapshot.value, options)
        outcome = cached.outcome(CacheStage.CODE_MAP)
        if cached.value is not None:
            code_map = cached.value
        else:
            code_map = self.extraction.generate_map(language, snapshot.value.extraction)
            self.cli.store_code_map(snapshot.value, code_map, options)
            outcome = outcome.model_copy(update={"computed": 1, "stored": 1})
        return CachedResult(value=code_map, outcomes=(*snapshot.outcomes, outcome))

    def generate_queryable_map_cached(
        self, language: str, root: str, policy: ScanPolicy, options: CacheOptions
    ) -> QueryableCodeMap:
        """Return a queryable code map with content-addressed persistent reuse."""

        return self.generate_queryable_map_cached_with_diagnostics(language, root, policy, options).value

    def generate_queryable_map_cached_with_diagnostics(
        self, language: str, root: str, policy: ScanPolicy, options: CacheOptions
    ) -> CachedResult[QueryableCodeMap]:
        """Return a queryable code map and public outcomes for every applicable cache stage."""

        cached = self.generate_map_cached_with_diagnostics(language, root, policy, options)
        return CachedResult(value=QueryableCodeMap(code_map=cached.value), outcomes=cached.outcomes)

    def clear_cache(self, options: CacheOptions) -> None:
        """Clear only the Modwire-owned directory for one cache namespace."""

        self.cli.clear_cache(options)

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        """Load and validate an architecture configuration from a directory."""

        return self.cli.load_configuration(str(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        """Create project-local Modwire configuration and agent guidance."""

        return self.cli.initialize(str(root), str(dot_dir), force)

    def generate_documentation(self, readme: str, check: bool) -> int:
        """Generate this README from the published interface docstrings, or check that it is current."""

        return self.cli.generate_documentation(
            str(readme), (type(self), CacheStage, CacheOutcome, CachedResult, CacheOptions, ScanPolicy), check
        )

    def run_extractor(self, language: str) -> int:
        """Run the native extractor transport for one supported language."""

        return self.cli.run_extractor(language)

    def run(self, argv: Sequence[str]) -> int:
        """Run the Modwire command line interface and return its process status."""

        return self.cli.run(argv)
