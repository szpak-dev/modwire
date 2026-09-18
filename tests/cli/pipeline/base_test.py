from pathlib import Path

from ..base_test import CliTestCase


class NativeExtractionTestCase(CliTestCase):
    def fixture_root(self, language: str) -> Path:
        return self.repository / "tests/fixtures/languages" / language

    def extract_project(self, language: str):
        return self.application.generate_map(language, self.workspace, self.scan_policy())

    def fixture_map(self, language: str):
        return self.application.generate_queryable_map(
            language,
            self.fixture_root(language),
            self.configured_scan_policy(("ignored/**",), False),
        )

    def external_project(self) -> Path:
        external = self.workspace.parent / f"{self.workspace.name}-external"
        external.mkdir()
        (external / "example.py").write_text("class ExampleValue:\n    pass\n", encoding="utf-8")
        return external
