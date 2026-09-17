from collections.abc import Mapping
from dataclasses import dataclass

from wireup import injectable

from ..shared.code.models.queryable_code_map import QueryableCodeMap
from .config.application import ConfigApplication
from .config.models.architecture_config import ArchitectureConfig
from .report.application import ReportApplication
from .report.models.report_catalog import ReportCatalog
from .report.models.report_node import ReportNode


@injectable
@dataclass(frozen=True)
class ArchitectureFacade:
    """Expose architecture reports and their catalog to other contexts."""

    reports: ReportApplication
    configuration: ConfigApplication

    def catalog(self) -> ReportCatalog:
        return self.reports.reports()

    def analyze(self, code_map: QueryableCodeMap, config: ArchitectureConfig) -> tuple[ReportNode, ...]:
        return self.reports.report(code_map, config)

    def configure(self, values: Mapping[str, object]) -> ArchitectureConfig:
        return self.configuration.validate(values)
