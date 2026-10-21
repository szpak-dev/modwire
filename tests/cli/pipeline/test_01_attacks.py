import os

import pytest

from modwire.application import (
    DuplicateIdentityError,
    ExtractorError,
    SourceParseError,
    UnsupportedLanguageError,
)

from .base_test import NativeExtractionTestCase


class TestNativeExtractionAttacks(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("language", "name", "source"),
        (
            ("python", "example_invalid.py", "1example_invalid\n"),
            ("typescript", "example_invalid.ts", "export const = ;\n"),
            ("php", "example_invalid.php", "<?php\nfunction example_invalid(\n"),
            (
                "java",
                "ExampleInvalid.java",
                "class ExampleInvalid { void example_invalid( }\n",
            ),
        ),
    )
    def test_reports_native_parser_failure(
        self,
        language: str,
        name: str,
        source: str,
    ) -> None:
        self.write_files({name: source})
        with pytest.raises(SourceParseError) as raised:
            self.extract_project(language)
        assert raised.value.language == language
        assert raised.value.path.endswith(name)
        assert raised.value.line > 0
        assert raised.value.column > 0
        assert isinstance(raised.value.__cause__, ExtractorError)

    def test_extraction_recovers_after_a_source_parse_failure(self) -> None:
        self.write_files({"example.py": "def example_invalid(:\n"})
        with pytest.raises(SourceParseError):
            self.extract_project("python")

        self.write_files({"example.py": "def example_valid():\n    return 1\n"})
        recovered = self.extract_project("python")

        assert tuple(recovered.extraction.files) == ("example.py",)

    def test_reports_missing_runtime_from_process_environment(self) -> None:
        self.write_project(1)
        result = self.run_cli_with_environment(
            ("report", "--language", "typescript"),
            {**os.environ, "PATH": ""},
        )
        assert result.returncode != 0
        assert "typescript extractor runtime is not available on PATH: node" in result.stderr

    def test_rejects_an_unsupported_language(self) -> None:
        with pytest.raises(UnsupportedLanguageError) as raised:
            self.extract_project("example_unknown")
        assert raised.value.language == "example_unknown"
        assert raised.value.supported_languages == ("python", "typescript", "php", "java")

    def test_reports_duplicate_module_identities(self) -> None:
        self.write_files(
            {
                "example_component.ts": "export const example_value = 1;\n",
                "example_component.tsx": "export const example_view = <div />;\n",
            }
        )
        with pytest.raises(DuplicateIdentityError) as raised:
            self.extract_project("typescript")
        assert raised.value.identity == "example_component"
        assert raised.value.existing_file_id == "example_component.ts"
        assert raised.value.duplicate_file_id == "example_component.tsx"
