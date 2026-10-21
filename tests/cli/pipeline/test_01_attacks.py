import os

import pytest

from modwire.application import (
    DuplicateIdentityError,
    ExtractorError,
    ExtractorExecutionError,
    SourceParseError,
    UnsupportedLanguageError,
)

from .base_test import NativeExtractionTestCase


class TestNativeExtractionAttacks(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("language", "name", "source", "failure_type"),
        (
            ("python", "example_invalid.py", "1example_invalid\n", SourceParseError),
            ("typescript", "example_invalid.ts", "export const = ;\n", ExtractorExecutionError),
            ("php", "example_invalid.php", "<?php\nfunction example_invalid(\n", ExtractorExecutionError),
            (
                "java",
                "ExampleInvalid.java",
                "class ExampleInvalid { void example_invalid( }\n",
                ExtractorExecutionError,
            ),
        ),
    )
    def test_reports_native_parser_failure(
        self,
        language: str,
        name: str,
        source: str,
        failure_type: type[ExtractorError],
    ) -> None:
        self.write_files({name: source})
        with pytest.raises(failure_type) as raised:
            self.extract_project(language)
        assert raised.value.language == language
        if isinstance(raised.value, SourceParseError):
            assert raised.value.path.endswith(name)
            assert raised.value.line == 1
            assert raised.value.column > 0
            assert isinstance(raised.value.__cause__, ExtractorExecutionError)
        else:
            assert raised.value.exit_code != 0

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
