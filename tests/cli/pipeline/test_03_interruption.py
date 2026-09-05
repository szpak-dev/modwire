import pytest

from .base_test import NativeExtractionTestCase


class TestBatchFailure(NativeExtractionTestCase):
    def test_a_late_invalid_file_prevents_returning_a_partial_map_and_allows_recovery(self) -> None:
        sources = {f"example_{index:04d}.py": "class ExampleValue: pass\n" for index in range(501)}
        sources["example_0500.py"] = "class 1example:\n"
        self.write_files(sources)
        with pytest.raises(RuntimeError, match="python extractor failed"):
            self.extract_project("python")
        self.write_files({"example_0500.py": "class ExampleRecovered: pass\n"})
        result = self.extract_project("python")
        assert set(result.extraction.files) == set(sources)
        assert result.extraction.files["example_0500.py"].classes[0].name == "ExampleRecovered"
