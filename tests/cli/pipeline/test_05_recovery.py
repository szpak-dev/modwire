import pytest

from .base_test import NativeExtractionTestCase


class TestExtractionRecovery(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("language", "name", "invalid", "valid"),
        (
            ("python", "example.py", "class 1example:\n", "class ExampleValue: pass\n"),
            ("typescript", "example.ts", "export class {", "export class ExampleValue {}\n"),
            ("php", "example.php", "<?php class {", "<?php class ExampleValue {}\n"),
        ),
    )
    def test_failed_extraction_does_not_poison_the_application(
        self, language: str, name: str, invalid: str, valid: str
    ) -> None:
        self.write_files({name: invalid})
        with pytest.raises(RuntimeError):
            self.extract_project(language)
        self.write_files({name: valid})
        result = self.extract_project(language)
        assert tuple(result.extraction.files) == (name,)
        assert result.extraction.files[name].classes[0].name == "ExampleValue"

    def test_removed_sources_disappear_on_the_next_request(self) -> None:
        self.write_files({"example_first.py": "", "example_second.py": ""})
        assert len(self.extract_project("python").extraction.files) == 2
        (self.workspace / "example_first.py").unlink()
        assert tuple(self.extract_project("python").extraction.files) == ("example_second.py",)

    def test_source_changes_are_visible_to_the_same_application(self) -> None:
        self.write_files({"example.py": "class ExampleFirst: pass\n"})
        assert self.extract_project("python").extraction.files["example.py"].classes[0].name == "ExampleFirst"
        self.write_files({"example.py": "class ExampleSecond: pass\n"})
        assert self.extract_project("python").extraction.files["example.py"].classes[0].name == "ExampleSecond"
