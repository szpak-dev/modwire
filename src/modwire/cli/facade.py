from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from modwire.architecture.config.models.architecture_config import ArchitectureConfig
from modwire.architecture.facade import ArchitectureFacade
from modwire.cli.initialization.application import InitializationApplication
from modwire.cli.pipeline.application import PipelineApplication
from modwire.cli.pipeline.models.command_request import CommandRequest
from modwire.extraction.facade import ExtractionFacade
from modwire.shared.code.models.code_map import CodeMap
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap


@injectable
@dataclass(frozen=True)
class CliFacade:
    """Coordinate initialization, extraction, architecture analysis and presentation."""

    architecture: ArchitectureFacade
    extraction: ExtractionFacade
    initialization: InitializationApplication
    pipeline: PipelineApplication

    def parse(self, argv: Sequence[str]) -> CommandRequest:
        return self.pipeline.parse(argv)

    def load_configuration(self, dot_dir: Path) -> ArchitectureConfig:
        return self.pipeline.load_configuration(dot_dir)

    def run(self, request: CommandRequest) -> int:
        if request.command == "init":
            return self.initialization.initialize(Path.cwd(), request.dot_dir, request.force)
        code_map = self.generate_queryable_map(
            request.language, request.architecture_root, self.architecture.excluded_patterns()
        )
        reports = self.architecture.analyze(code_map)
        return self.pipeline.run(reports, summary=request.summary)

    def discover(self, root: Path, excluded_patterns: tuple[str, ...]) -> tuple[str, ...]:
        """Return supported languages found under the supplied source directory."""
        return tuple(
            language
            for language in self.extraction.supported_languages()
            if self.pipeline.has_source_files(
                self.extraction.request(language, root).model_copy(update={"excluded_patterns": excluded_patterns})
            )
        )

    def generate_map(self, language: str, root: Path, excluded_patterns: tuple[str, ...]) -> CodeMap:
        """Read a project through its native extractor and return its dependency map."""
        request = self.extraction.request(language, root).model_copy(update={"excluded_patterns": excluded_patterns})
        return self.extraction.generate_map(language, self.pipeline.extract(request))

    def generate_queryable_map(
        self, language: str, root: Path, excluded_patterns: tuple[str, ...]
    ) -> QueryableCodeMap:
        """Read a project and expose queryable source symbols and dependencies."""
        return QueryableCodeMap(code_map=self.generate_map(language, root, excluded_patterns))

    def parse_python_command(self) -> int:
        request = self.pipeline.read_python()
        if request is None:
            return 1
        if request.batch:
            result: dict[str, object] = {
                source.source_id: self.extraction.parse_python(
                    source.content, source.path, source.root, source.source_id
                )
                for source in request.sources
            }
            return self.pipeline.write_python(result)
        source = request.sources[0]
        return self.pipeline.write_python(
            self.extraction.parse_python(source.content, source.path, source.root, source.source_id)
        )
