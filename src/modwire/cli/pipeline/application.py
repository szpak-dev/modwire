from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from modwire.architecture.config.models.architecture_config import ArchitectureConfig
from modwire.architecture.report.models.report_node import ReportNode
from modwire.cli.pipeline.domain import ReportPipelineStep, SourceReader
from modwire.cli.pipeline.models.command_request import CommandRequest
from modwire.cli.pipeline.models.python_command_input import PythonCommandInput
from modwire.cli.pipeline.models.report_pipeline_context import ReportPipelineContext
from modwire.cli.pipeline.services.command_line import CommandLine
from modwire.cli.pipeline.services.configuration_loader import ConfigurationLoader
from modwire.cli.pipeline.services.python_parser_command import PythonParserCommand
from modwire.extraction.extractors.models.extraction_request import ExtractionRequest
from modwire.shared.code.models.source_extraction import SourceExtraction


@injectable()
@dataclass(frozen=True)
class PipelineApplication:
    """Run ordered report-rendering steps and return their exit status."""

    steps: Mapping[Hashable, ReportPipelineStep]
    commands: CommandLine
    configuration: ConfigurationLoader
    reader: SourceReader
    python: PythonParserCommand

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

    def read_python(self) -> PythonCommandInput | None:
        return self.python.read()

    def write_python(self, result: dict[str, object]) -> int:
        return self.python.write(result)

    def run(self, reports: tuple[ReportNode, ...], *, summary: bool) -> int:
        context = ReportPipelineContext(reports=reports, summary=summary)
        result = self.process(context)
        return int(result.failed)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        for _, step in sorted(self.steps.items(), key=lambda item: int(str(item[0]).partition("-")[0])):
            if step.should_process(context):
                context = step.process(context)
        return context
