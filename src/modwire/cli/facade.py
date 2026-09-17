from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..architecture.facade import ArchitectureFacade
from ..architecture.config.models.architecture_config import ArchitectureConfig
from ..architecture.report.models.report_node import ReportNode
from ..extraction.facade import ExtractionFacade
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
    architecture: ArchitectureFacade
    extraction: ExtractionFacade
    initialization: InitializationApplication
    pipeline: PipelineApplication
    documentation: DocumentationApplication

    def working_directory(self) -> str:
        return str(Path.cwd())

    def parse(self, argv: Sequence[str]) -> CommandRequest:
        return self.pipeline.parse(argv)

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        return self.pipeline.load_configuration(Path(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        return self.initialization.initialize(Path(root), Path(dot_dir), force)

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

    def generate_documentation(self, readme: str, check: bool, description: str) -> int:
        return self.documentation.generate(Path(readme), check, description)

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
        config = self.load_configuration(str(request.dot_dir))
        extraction = self.extract(
            self.extraction.request(request.language, str(request.architecture_root)).model_copy(
                update={"excluded_patterns": config.excluded_patterns}
            )
        )
        code_map = self.extraction.generate_queryable_map(request.language, extraction)
        return self.render(self.architecture.analyze(code_map, config), request.summary)
