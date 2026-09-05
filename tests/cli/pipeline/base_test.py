from pathlib import Path

from modwire.shared import CodeMap, QueryableCodeMap
from tests.cli.base_test import CliTestCase


class NativeExtractionTestCase(CliTestCase):
    def fixture_root(self, language: str) -> Path:
        return self.repository / "tests/fixtures/languages" / language

    def extract_project(self, language: str) -> CodeMap:
        return self.cli().generate_map(language, self.workspace, ())

    def fixture_map(self, language: str) -> QueryableCodeMap:
        return self.cli().generate_queryable_map(language, self.fixture_root(language), ())
