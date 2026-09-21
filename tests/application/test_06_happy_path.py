from modwire.application import ModwireApplication

from .base_test import ApplicationTestCase


class TestModwireApplication(ApplicationTestCase):
    def test_repeated_construction_returns_independent_applications(self) -> None:
        application = ModwireApplication.create()
        assert application is not self.application
        assert application.architecture is not self.application.architecture
        assert application.cli is not self.application.cli
        assert application.extraction is not self.application.extraction

    def test_public_application_exposes_the_report_catalog(self) -> None:
        assert tuple(item.id for item in self.application.catalog().reports) == (
            "architecture.map",
            "architecture.violations.flow",
            "architecture.violations.shape",
            "architecture.insights",
        )

    def test_installed_distribution_configures_maps_and_reports_source(self) -> None:
        project = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        result = self.installed_consumer(project, "python")
        assert result.returncode == 0, result.stderr
