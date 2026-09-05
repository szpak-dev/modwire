from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.insights.domain import InsightReporterInterface
from modwire.architecture.insights.models.exports_report import ExportsReport
from modwire.architecture.insights.models.exports_report_item import ExportsReportItem
from modwire.architecture.map.models.architecture_map import ArchitectureMap


@injectable(as_type=InsightReporterInterface, qualifier="exports")
@dataclass(frozen=True)
class ExportsReporter(InsightReporterInterface):
    @property
    def name(self) -> str:
        return "unused-exports"

    @property
    def report_type(self) -> type[ExportsReport]:
        return ExportsReport

    def collect(self, architecture_map: ArchitectureMap) -> ExportsReport:
        imported_names = self.imported_names(architecture_map)
        unused_exports = tuple(
            ExportsReportItem(
                source_id=export_result.source_id,
                name=export.name,
                kind=export.kind,
                crossing_type=export.crossing_type,
                reason="not imported",
            )
            for export_result in sorted(
                architecture_map.code_map.exports().all(), key=lambda result: (result.source_id, result.item.name)
            )
            if (export := export_result.item).name not in imported_names and export.local_name not in imported_names
        )
        return self.report_type(unused_exports=unused_exports)

    def imported_names(self, architecture_map: ArchitectureMap) -> set[str]:
        imported_names: set[str] = set()
        for import_result in architecture_map.code_map.imports().all():
            imported_name = import_result.item.imported_name
            if imported_name:
                imported_names.add(imported_name)
            for imported_symbol in import_result.item.imported_symbols:
                imported_names.add(imported_symbol.name)
                if imported_symbol.alias:
                    imported_names.add(imported_symbol.alias)
        return imported_names
