import pytest

from modwire.application import ExtractorExecutionError

from ..base_test import ExtractionTestCase


class TestPythonAttacks(ExtractionTestCase):
    def test_rejects_invalid_python_source(self) -> None:
        with pytest.raises(ExtractorExecutionError) as raised:
            self.extract({"src/example_invalid.py": "1example_invalid\n"})
        assert raised.value.language == "python"
        assert raised.value.exit_code != 0

    def test_preserves_nested_source_identity(self) -> None:
        result = self.extract({"example_virtual/example.py": "class ExampleValue:\n    pass\n"})
        assert result.source_ids() == ("example_virtual/example.py",)
        assert result.classes().first().item.name == "ExampleValue"
