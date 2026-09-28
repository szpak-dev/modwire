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
from .cli.cache.models.cache_outcome import CacheOutcome
from .cli.cache.models.cache_stage import CacheStage
from .cli.cache.models.cached_result import CachedResult
from .cli.facade import CliFacade
from .extraction.facade import ExtractionFacade
from .implementation.facade import ImplementationFacade
from .implementation.manifest.models.digest_algorithm import DigestAlgorithm
from .implementation.manifest.models.implementation_manifest import ImplementationManifest
from .implementation.manifest.models.implementation_manifest_document import ImplementationManifestDocument
from .implementation.manifest.models.manifest_format import ManifestFormat
from .shared.code.models.capability_coverage import CapabilityCoverage
from .shared.code.models.capability_status import CapabilityStatus
from .shared.code.models.code_map import CodeMap
from .shared.code.models.declaration_family import DeclarationFamily
from .shared.code.models.declaration_identity import DeclarationIdentity
from .shared.code.models.fact_capability import FactCapability
from .shared.code.models.queryable_code_map import QueryableCodeMap
from .shared.code.models.scan_policy import ScanPolicy
from .shared.code.models.source_manifest_identity import SourceManifestIdentity
from .shared.code.models.source_member_kind import SourceMemberKind
from .shared.code.models.source_relation_kind import SourceRelationKind

__all__ = [
    "CacheOptions",
    "CacheOutcome",
    "CacheStage",
    "CachedResult",
    "CodeMap",
    "CapabilityCoverage",
    "CapabilityStatus",
    "DeclarationFamily",
    "DeclarationIdentity",
    "DigestAlgorithm",
    "FactCapability",
    "ImplementationManifest",
    "ImplementationManifestDocument",
    "ManifestFormat",
    "ModwireApplication",
    "QueryableCodeMap",
    "ScanPolicy",
    "SourceMemberKind",
    "SourceManifestIdentity",
    "SourceRelationKind",
]


@dataclass(frozen=True)
class ModwireApplication:
    """Public entry point for extraction, implementation manifests, architecture analysis, and the Modwire CLI."""

    architecture: ArchitectureFacade
    cli: CliFacade
    extraction: ExtractionFacade
    implementation: ImplementationFacade

    @classmethod
    def create(cls) -> Self:
        """Create an isolated application with all services resolved through Wireup."""

        container = create_sync_container(injectables=[modwire])
        try:
            return cls(
                architecture=container.get(ArchitectureFacade),
                cli=container.get(CliFacade),
                extraction=container.get(ExtractionFacade),
                implementation=container.get(ImplementationFacade),
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
            self.cli.maintain_cache(options)
            return CachedResult(value=cached.value, outcomes=cached.outcomes)
        reports = self.architecture.analyze(code_map, config)
        self.cli.store_reports(code_map.code_map, config, reports, options)
        self.cli.maintain_cache(options)
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
        return self.extraction.generate_map(request, self.cli.extract(request, policy))

    def generate_queryable_map(self, language: str, root: str, policy: ScanPolicy) -> QueryableCodeMap:
        """Extract source files and return a queryable code map."""

        return QueryableCodeMap(code_map=self.generate_map(language, root, policy))

    def generate_map_cached(self, language: str, root: str, policy: ScanPolicy, options: CacheOptions) -> CodeMap:
        """Return a code map with content-addressed source and complete-source-set reuse."""

        return self.generate_map_cached_with_diagnostics(language, root, policy, options).value

    def generate_map_cached_with_diagnostics(
        self, language: str, root: str, policy: ScanPolicy, options: CacheOptions
    ) -> CachedResult[CodeMap]:
        """Return a code map and public outcomes for extraction and complete-map reuse."""

        request = self.extraction.request(language, str(root))
        plan = self.cli.prepare_cache(request, policy)
        cached = self.cli.cached_code_map(plan, options)
        outcome = cached.outcome(CacheStage.CODE_MAP)
        if cached.value is not None:
            code_map = cached.value
            extraction_outcomes = (
                CacheOutcome(
                    stage=CacheStage.EXTRACTION,
                    namespace=options.namespace,
                    hits=len(plan.sources),
                ),
            )
        else:
            sources = self.cli.cached_sources(request, plan, options)
            self.cli.maintain_source_set(plan, options)
            code_map = self.extraction.generate_map(request, sources.value)
            self.cli.store_code_map(plan, code_map, options)
            outcome = outcome.model_copy(update={"computed": 1, "stored": 1})
            extraction_outcomes = sources.outcomes
        self.cli.maintain_cache(options)
        return CachedResult(value=code_map, outcomes=(*extraction_outcomes, outcome))

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

    def source_manifest_identity(self, language: str, root: str, policy: ScanPolicy) -> SourceManifestIdentity:
        """Observe the current canonical source-manifest identity without parsing source."""

        request = self.extraction.request(language, str(root))
        return self.cli.source_manifest_identity(request, policy)

    def implementation_manifest(self, code_map: CodeMap, format: ManifestFormat) -> ImplementationManifestDocument:
        """Publish a deterministic, provenance-bearing implementation manifest."""

        return self.implementation.manifest(code_map, format)

    def implementation_manifest_formats(self) -> tuple[ManifestFormat, ...]:
        """Return the implementation-manifest formats registered in this application."""

        return self.implementation.formats()

    def read_implementation_manifest(self, document: ImplementationManifestDocument) -> ImplementationManifest:
        """Read and canonically validate a serialized implementation manifest."""

        return self.implementation.read(document)

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
            str(readme),
            (
                type(self),
                CacheStage,
                CacheOutcome,
                CachedResult,
                CacheOptions,
                ScanPolicy,
                SourceManifestIdentity,
                SourceMemberKind,
                SourceRelationKind,
                ImplementationManifest,
                ImplementationManifestDocument,
                ManifestFormat,
                DeclarationFamily,
                DeclarationIdentity,
                DigestAlgorithm,
                FactCapability,
                CapabilityStatus,
                CapabilityCoverage,
            ),
            check,
        )

    def run_extractor(self, language: str) -> int:
        """Run the native extractor transport for one supported language."""

        return self.cli.run_extractor(language)

    def run(self, argv: Sequence[str]) -> int:
        """Run the Modwire command line interface and return its process status."""

        return self.cli.run(argv)
