from pathlib import Path

from ..base_test import CliTestCase


class NativeExtractionTestCase(CliTestCase):
    def fixture_root(self, language: str) -> Path:
        return self.repository / "tests/fixtures/languages" / language

    def extract_project(self, language: str):
        return self.application.generate_map(language, self.workspace, ())

    def fixture_map(self, language: str):
        return self.application.generate_queryable_map(language, self.fixture_root(language), ())
