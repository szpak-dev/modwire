import json

import pytest

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

    @pytest.mark.parametrize("language", ("python", "ruby"))
    def test_installed_distribution_configures_maps_and_reports_source(self, language: str) -> None:
        project = self.repository / "tests/fixtures/extraction_lifecycle" / language / "valid"
        result = self.installed_consumer(project, language)
        assert result.returncode == 0, result.stderr

    @pytest.mark.parametrize("language", ("typescript", "ruby"))
    def test_installed_distribution_reports_non_python_parse_failure(self, language: str) -> None:
        project = self.repository / "tests/fixtures/extraction_lifecycle" / language / "invalid"
        result = self.installed_failure_consumer(project, language)

        assert result.returncode == 0, result.stderr
        failure = json.loads(result.stdout)
        assert failure["type"] == "SourceParseError"
        assert failure["language"] == language
        assert failure["path"].endswith(next(project.iterdir()).name)
        assert failure["line"] > 0
        assert failure["column"] > 0
        assert failure["diagnostic"]
