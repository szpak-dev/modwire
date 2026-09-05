from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ...architecture.config.models.architecture_config import ArchitectureConfig
from ...architecture.report.models.report_node import ReportNode
from ...extraction.extractors.models.extraction_request import ExtractionRequest
from ...shared.code.models.source_extraction import SourceExtraction
from .domain import ReportPipelineStep, SourceReader
from .models.command_request import CommandRequest
from .models.extractor_command_input import ExtractorCommandInput
from .models.report_pipeline_context import ReportPipelineContext
from .services.command_line import CommandLine
from .services.configuration_loader import ConfigurationLoader
from .services.extractor_command import ExtractorCommand


@injectable()
@dataclass(frozen=True)
class PipelineApplication:
    """Run ordered report-rendering steps and return their exit status."""

    steps: Mapping[Hashable, ReportPipelineStep]
    commands: CommandLine
    configuration: ConfigurationLoader
    reader: SourceReader
    extractor_command: ExtractorCommand

    def parse(self, argv: Sequence[str]) -> CommandRequest:
        return self.commands.parse(argv)

    def load_configuration(self, dot_dir: Path) -> ArchitectureConfig:
        return self.configuration.load(dot_dir)

    def extract(self, request: ExtractionRequest) -> SourceExtraction:
        self.reader.ensure_available(request.runtime)
        return self.reader.extract_source(request)

    def has_source_files(self, request: ExtractionRequest) -> bool:
        self.reader.ensure_available(request.runtime)
        return self.reader.has_source_files(request)

    def read_sources(self, language: str) -> ExtractorCommandInput | None:
        return self.extractor_command.read(language)

    def write_sources(self, result: dict[str, object]) -> int:
        return self.extractor_command.write(result)

    def run(self, reports: tuple[ReportNode, ...], *, summary: bool) -> int:
        context = ReportPipelineContext(reports=reports, summary=summary)
        result = self.process(context)
        return int(result.failed)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        for _, step in sorted(self.steps.items(), key=lambda item: int(str(item[0]).partition("-")[0])):
            if step.should_process(context):
                context = step.process(context)
        return context
