import pytest

from modwire.application import ExtractorExecutionError, SourceParseError

from ..base_test import ExtractionTestCase


class TestPythonAttacks(ExtractionTestCase):
    def test_rejects_invalid_python_source(self) -> None:
        with pytest.raises(SourceParseError) as raised:
            self.extract({"src/example_invalid.py": "1example_invalid\n"})
        assert raised.value.language == "python"
        assert raised.value.path.endswith("src/example_invalid.py")
        assert raised.value.line == 1
        assert raised.value.column == 1
        assert isinstance(raised.value.__cause__, ExtractorExecutionError)

    def test_preserves_nested_source_identity(self) -> None:
        result = self.extract({"example_virtual/example.py": "class ExampleValue:\n    pass\n"})
        assert result.source_ids() == ("example_virtual/example.py",)
        assert result.classes().first().item.name == "ExampleValue"
