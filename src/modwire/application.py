from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from wireup import injectable

from .architecture.config.models.architecture_config import ArchitectureConfig
from .architecture.facade import ArchitectureFacade
from .architecture.report.models.report_catalog import ReportCatalog
from .architecture.report.models.report_node import ReportNode
from .cli.facade import CliFacade
from .extraction.facade import ExtractionFacade
from .shared.code.models.code_map import CodeMap
from .shared.code.models.queryable_code_map import QueryableCodeMap


@injectable
@dataclass(frozen=True)
class ModwireApplication:
    """Coordinate code extraction, architecture analysis and CLI actions."""

    architecture: ArchitectureFacade
    cli: CliFacade
    extraction: ExtractionFacade

    def configure(self, values: Mapping[str, object]) -> ArchitectureConfig:
        """Validate a configuration document and return immutable typed configuration."""
        return self.architecture.configure(values)

    def catalog(self) -> ReportCatalog:
        """Describe the available reports and their nested sections."""
        return self.architecture.catalog()

    def analyze(self, code_map: QueryableCodeMap, config: ArchitectureConfig) -> tuple[ReportNode, ...]:
        """Analyze a supplied map under the explicit configuration for this call."""
        return self.architecture.analyze(code_map, config)

    def discover(self, root: str, excluded_patterns: tuple[str, ...]) -> tuple[str, ...]:
        """Discover supported source languages beneath a directory."""
        return tuple(
            language
            for language in self.extraction.supported_languages()
            if self.cli.has_source_files(
                self.extraction.request(language, str(root)).model_copy(update={"excluded_patterns": excluded_patterns})
            )
        )

    def generate_map(self, language: str, root: str, excluded_patterns: tuple[str, ...]) -> CodeMap:
        """Read a project through its native extractor and return its dependency map."""
        request = self.extraction.request(language, str(root)).model_copy(
            update={"excluded_patterns": excluded_patterns}
        )
        return self.extraction.generate_map(language, self.cli.extract(request))

    def generate_queryable_map(self, language: str, root: str, excluded_patterns: tuple[str, ...]) -> QueryableCodeMap:
        """Read a project and expose queryable source symbols and dependencies."""
        return QueryableCodeMap(code_map=self.generate_map(language, root, excluded_patterns))

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        """Read and validate a project's architecture configuration through CLI I/O."""
        return self.cli.load_configuration(str(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        """Create project guidance while preserving existing files unless forced."""
        return self.cli.initialize(str(root), str(dot_dir), force)

    def generate_documentation(self, readme: str, check: bool) -> int:
        """Update or verify the public command reference."""
        return self.cli.generate_documentation(str(readme), check, self.run.__doc__ or "")

    def run_extractor(self, language: str) -> int:
        """Run a bundled extractor's source-input and JSON-output command protocol."""
        request = self.cli.read_sources(language)
        if request is None:
            return 1
        if request.batch:
            result: dict[str, object] = {
                source.source_id: self.extraction.parse_source(
                    language, source.content, str(source.path), str(source.root), source.source_id
                )
                for source in request.sources
            }
            return self.cli.write_sources(result)
        source = request.sources[0]
        return self.cli.write_sources(
            self.extraction.parse_source(language, source.content, str(source.path), str(source.root), source.source_id)
        )

    def run(self, argv: Sequence[str]) -> int:
        """Provide `modwire init` for setup and `modwire report` for architecture feedback.

        Existing `modwire --language <language>` automation continues to run reports.
        """
        request = self.cli.parse(argv)
        if request.command == "init":
            return self.initialize(self.cli.working_directory(), str(request.dot_dir), request.force)
        config = self.load_configuration(str(request.dot_dir))
        code_map = self.generate_queryable_map(
            request.language, str(request.architecture_root), config.excluded_patterns
        )
        return self.cli.render(self.analyze(code_map, config), request.summary)
