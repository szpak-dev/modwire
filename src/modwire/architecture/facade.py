from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.application import ConfigApplication
from modwire.architecture.report.application import ReportApplication
from modwire.architecture.report.models.report_catalog import ReportCatalog
from modwire.architecture.report.models.report_node import ReportNode
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap


@injectable
@dataclass(frozen=True)
class ArchitectureFacade:
    """Expose architecture reports and their catalog to other contexts."""

    reports: ReportApplication
    configuration: ConfigApplication

    def catalog(self) -> ReportCatalog:
        return self.reports.reports()

    def analyze(self, code_map: QueryableCodeMap) -> tuple[ReportNode, ...]:
        return self.reports.report(code_map)

    def excluded_patterns(self) -> tuple[str, ...]:
        return self.configuration.current().excluded_patterns
