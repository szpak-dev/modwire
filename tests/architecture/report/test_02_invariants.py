from modwire.architecture import ArchitectureFacade, MapReport
from tests.architecture.base_test import ArchitectureTestCase


class TestReportInvariants(ArchitectureTestCase):
    def test_catalog_exposes_each_preserved_report(self) -> None:
        catalog = self.service(ArchitectureFacade, self.example_configuration()).catalog()
        assert tuple(report.id for report in catalog.reports) == (
            "architecture.map", "architecture.violations.flow", "architecture.violations.shape", "architecture.insights",
        )
        assert tuple(child.id for child in catalog.reports[-1].children) == (
            "architecture.insights.clusters", "architecture.insights.hotspots", "architecture.insights.coherence",
            "architecture.insights.callables", "architecture.insights.exports",
        )

    def test_repeated_analysis_preserves_values_and_input(self) -> None:
        config = self.example_configuration()
        source = self.queryable_map(("src/example.py",), ())
        before = source.code_map.to_json()
        facade = self.service(ArchitectureFacade, config)
        assert facade.analyze(source) == facade.analyze(source)
        assert source.code_map.to_json() == before

    def test_map_reports_unclassified_sources(self) -> None:
        report = self.report(MapReport, self.example_configuration(), self.queryable_map(("example.py",), ()))
        assert report.unknown_files == ("example.py",)
