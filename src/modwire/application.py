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
from .extraction.facade import ExtractionFacade
from .shared.code.models.code_map import CodeMap
from .shared.code.models.queryable_code_map import QueryableCodeMap


@dataclass(frozen=True)
class ModwireApplication:
    architecture: ArchitectureFacade
    cli: CliFacade
    extraction: ExtractionFacade

    @classmethod
    def create(cls) -> Self:
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
        return self.architecture.configure(values)

    def catalog(self) -> ReportCatalog:
        return self.architecture.catalog()

    def analyze(self, code_map: QueryableCodeMap, config: ArchitectureConfig) -> tuple[ReportNode, ...]:
        return self.architecture.analyze(code_map, config)

    def discover(self, root: str, excluded_patterns: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            language
            for language in self.extraction.supported_languages()
            if self.cli.has_source_files(
                self.extraction.request(language, str(root)).model_copy(update={"excluded_patterns": excluded_patterns})
            )
        )

    def generate_map(self, language: str, root: str, excluded_patterns: tuple[str, ...]) -> CodeMap:
        request = self.extraction.request(language, str(root)).model_copy(
            update={"excluded_patterns": excluded_patterns}
        )
        return self.extraction.generate_map(language, self.cli.extract(request))

    def generate_queryable_map(self, language: str, root: str, excluded_patterns: tuple[str, ...]) -> QueryableCodeMap:
        return QueryableCodeMap(code_map=self.generate_map(language, root, excluded_patterns))

    def load_configuration(self, dot_dir: str) -> ArchitectureConfig:
        return self.cli.load_configuration(str(dot_dir))

    def initialize(self, root: str, dot_dir: str, force: bool) -> int:
        return self.cli.initialize(str(root), str(dot_dir), force)

    def generate_documentation(self, readme: str, check: bool) -> int:
        return self.cli.generate_documentation(str(readme), check, self.run.__doc__ or "")

    def run_extractor(self, language: str) -> int:
        return self.cli.run_extractor(language)

    def run(self, argv: Sequence[str]) -> int:
        return self.cli.run(argv)
