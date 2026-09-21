from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from wireup import create_sync_container

import modwire

from .architecture.config.models.architecture_config import ArchitectureConfig
from .architecture.facade import ArchitectureFacade
from .architecture.report.models.report_catalog import ReportCatalog
from .architecture.report.models.report_node import ReportNode
from .cli.facade import CliFacade
from .cli.pipeline.models.scan_policy import ScanPolicy
from .extraction.facade import ExtractionFacade
from .shared.code.models.code_map import CodeMap
from .shared.code.models.queryable_code_map import QueryableCodeMap

__all__ = ["CodeMap", "ModwireApplication", "QueryableCodeMap", "ScanPolicy"]


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

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        """Load and validate an architecture configuration from a directory."""

        return self.cli.load_configuration(str(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        """Create project-local Modwire configuration and agent guidance."""

        return self.cli.initialize(str(root), str(dot_dir), force)

    def generate_documentation(self, readme: str, check: bool) -> int:
        """Generate this README from the published interface docstrings, or check that it is current."""

        return self.cli.generate_documentation(str(readme), (type(self), ScanPolicy), check)

    def run_extractor(self, language: str) -> int:
        """Run the native extractor transport for one supported language."""

        return self.cli.run_extractor(language)

    def run(self, argv: Sequence[str]) -> int:
        """Run the Modwire command line interface and return its process status."""

        return self.cli.run(argv)
