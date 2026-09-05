from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..architecture.config.models.architecture_config import ArchitectureConfig
from ..architecture.report.models.report_node import ReportNode
from ..extraction.extractors.models.extraction_request import ExtractionRequest
from ..shared.code.models.source_extraction import SourceExtraction
from .documentation.application import DocumentationApplication
from .initialization.application import InitializationApplication
from .pipeline.application import PipelineApplication
from .pipeline.models.command_request import CommandRequest
from .pipeline.models.extractor_command_input import ExtractorCommandInput


@injectable
@dataclass(frozen=True)
class CliFacade:
    """Own command input, filesystem access, native processes and presentation."""

    initialization: InitializationApplication
    pipeline: PipelineApplication
    documentation: DocumentationApplication

    def working_directory(self) -> Path:
        return Path.cwd()

    def parse(self, argv: Sequence[str]) -> CommandRequest:
        return self.pipeline.parse(argv)

    def load_configuration(self, dot_dir: Path) -> ArchitectureConfig:
        return self.pipeline.load_configuration(dot_dir)

    def initialize(self, root: Path, dot_dir: Path, force: bool) -> int:
        return self.initialization.initialize(root, dot_dir, force)

    def extract(self, request: ExtractionRequest) -> SourceExtraction:
        return self.pipeline.extract(request)

    def has_source_files(self, request: ExtractionRequest) -> bool:
        return self.pipeline.has_source_files(request)

    def render(self, reports: tuple[ReportNode, ...], summary: bool) -> int:
        return self.pipeline.run(reports, summary=summary)

    def read_sources(self, language: str) -> ExtractorCommandInput | None:
        return self.pipeline.read_sources(language)

    def write_sources(self, result: dict[str, object]) -> int:
        return self.pipeline.write_sources(result)

    def generate_documentation(self, readme: Path, check: bool, description: str) -> int:
        return self.documentation.generate(readme, check, description)
