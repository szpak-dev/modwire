import os

import pytest

from .base_test import NativeExtractionTestCase


class TestNativeExtractionAttacks(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("language", "name", "source"),
        (
            ("python", "example_invalid.py", "1example_invalid\n"),
            ("typescript", "example_invalid.ts", "export const = ;\n"),
            ("php", "example_invalid.php", "<?php\nfunction example_invalid(\n"),
        ),
    )
    def test_reports_native_parser_failure(self, language: str, name: str, source: str) -> None:
        self.write_files({name: source})
        with pytest.raises(RuntimeError, match=f"{language} extractor failed with exit code"):
            self.extract_project(language)

    def test_reports_missing_runtime_from_process_environment(self) -> None:
        self.write_project(1)
        result = self.run_cli_with_environment(
            ("report", "--language", "typescript"),
            {**os.environ, "PATH": ""},
        )
        assert result.returncode != 0
        assert "typescript extractor runtime is not available on PATH: node" in result.stderr

    def test_rejects_an_unsupported_language(self) -> None:
        with pytest.raises(ValueError, match="Language is not supported: example_unknown"):
            self.extract_project("example_unknown")

    def test_reports_duplicate_module_identities(self) -> None:
        self.write_files(
            {
                "example_component.ts": "export const example_value = 1;\n",
                "example_component.tsx": "export const example_view = <div />;\n",
            }
        )
        with pytest.raises(ValueError) as raised:
            self.extract_project("typescript")
        assert "example_component" in str(raised.value)
