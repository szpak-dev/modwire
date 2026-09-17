import pytest
from pydantic import ValidationError

from .base_test import ApplicationTestCase


class TestModwireApplicationAttacks(ApplicationTestCase):
    def test_invalid_configuration_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self.application.configure({"shape": {"realms": [{"name": "", "match": "src"}]}})

    def test_configuration_does_not_leak_between_calls(self) -> None:
        code_map = self.application.generate_queryable_map(
            "python",
            self.project({"src/example.py": "def example_function():\n    pass\n"}),
            (),
        )
        strict = self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
        permissive = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "src", "shape": {"max_functions_per_file": 1}}]}}
        )
        strict_reports = self.application.analyze(code_map, strict)
        permissive_reports = self.application.analyze(code_map, permissive)
        assert next(item for item in strict_reports if item.metadata.id == "architecture.violations.shape").violations
        assert not next(
            item for item in permissive_reports if item.metadata.id == "architecture.violations.shape"
        ).violations
        assert self.application.analyze(code_map, strict) == strict_reports
