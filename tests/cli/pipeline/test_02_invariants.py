import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from modwire.application import SourceCallResolution, SourceParseError, SourceScopeKind

from .base_test import NativeExtractionTestCase


class TestNativeExtractionInvariants(NativeExtractionTestCase):
    def test_native_languages_preserve_dependency_resolution(self) -> None:
        for language in self.application.extraction.supported_languages():
            result = self.fixture_map(language)
            assert result.tracked_dependency_edges().count() == 7, language
            assert result.external_dependency_edges().count() == 1, language
            assert result.code_map.extraction.files_excluded == 0, language
            assert result.code_map.extraction.directories_pruned == 1, language
            assert result.code_map.extraction.files_found == len(result.source_ids()), language

    def test_discovers_each_fixture_language(self) -> None:
        for language in self.application.extraction.supported_languages():
            assert self.application.discover(self.fixture_root(language), self.scan_policy()) == (language,)

    def test_configured_exclusions_remove_files_from_the_map(self) -> None:
        self.write_files(
            {
                "src/example.py": "class ExampleValue:\n    pass\n",
                "src/example_generated/example_invalid.py": "1example_invalid\n",
                "src/example_skip.py": "1example_invalid\n",
            }
        )
        result = self.application.generate_map(
            "python",
            self.workspace,
            self.configured_scan_policy(("src/example_generated/**", "src/example_skip.py"), False),
        )
        assert tuple(result.extraction.files) == ("src/example.py",)
        assert result.extraction.files_excluded == 1
        assert result.extraction.directories_pruned == 1

    def test_pruned_directory_descendants_receive_no_filesystem_operations(self) -> None:
        self.write_files(
            {
                "src/example.py": "class ExampleValue:\n    pass\n",
                "src/example_generated/nested/example.py": "class ExampleGenerated:\n    pass\n",
            }
        )
        excluded_root = (self.workspace / "src/example_generated").absolute()
        with patch("os.scandir", wraps=os.scandir) as record_scan:
            result = self.application.generate_map(
                "python",
                self.workspace,
                self.configured_scan_policy(("src/example_generated/**",), False),
            )

        assert tuple(result.extraction.files) == ("src/example.py",)
        assert result.extraction.files_excluded == 0
        assert result.extraction.directories_pruned == 1
        scanned_directories = (Path(call.args[0]).absolute() for call in record_scan.call_args_list)
        assert all(
            directory != excluded_root and excluded_root not in directory.parents for directory in scanned_directories
        )

    def test_hidden_directories_are_scanned_without_a_caller_exclusion(self) -> None:
        self.write_files({".example_hidden/example.py": "class ExampleValue:\n    pass\n"})
        result = self.application.generate_map("python", self.workspace, self.scan_policy())
        assert tuple(result.extraction.files) == (".example_hidden/example.py",)
        assert result.extraction.directories_pruned == 0

    def test_symlink_directories_are_not_followed_by_default(self) -> None:
        external = self.external_project()
        (self.workspace / "example_link").symlink_to(external, target_is_directory=True)
        result = self.application.generate_map("python", self.workspace, self.scan_policy())
        assert result.extraction.files == {}

    def test_caller_can_enable_symlink_directory_traversal(self) -> None:
        external = self.external_project()
        (self.workspace / "example_link").symlink_to(external, target_is_directory=True)
        result = self.application.generate_map("python", self.workspace, self.configured_scan_policy((), True))
        assert tuple(result.extraction.files) == ("example_link/example.py",)

    @pytest.mark.parametrize("fixture", ("nonliteral_import", "nonliteral_export"))
    def test_typescript_rejects_nonliteral_module_specifiers(self, fixture: str) -> None:
        shutil.copyfile(
            self.repository / "tests/fixtures/command_transport" / fixture / "example.ts",
            self.workspace / "example.ts",
        )
        with pytest.raises(SourceParseError) as raised:
            self.extract_project("typescript")

        assert raised.value.language == "typescript"
        assert raised.value.line == 1
        assert raised.value.column > 1
        assert "string literal" in raised.value.diagnostic

    def test_php_preserves_anonymous_class_construction(self) -> None:
        shutil.copyfile(
            self.repository / "tests/fixtures/command_transport/anonymous_class/example.php",
            self.workspace / "example.php",
        )
        result = self.extract_project("php")
        source = result.extraction.files["example.php"]
        factory, anonymous = source.declarations
        method = factory.methods[0]
        assert factory.name == "ExampleFactory"
        assert anonymous.placement.lexical_scope.kind is SourceScopeKind.DECLARATION
        assert anonymous.placement.lexical_scope.declaration_id == method.declaration_id
        assert len(source.calls) == 1
        assert source.calls[0].source_callable_id == method.declaration_id
        assert source.calls[0].resolution is SourceCallResolution.DYNAMIC

    def test_large_source_input_keeps_every_file_and_identity(self) -> None:
        names = tuple(f"example_{index:04d}.py" for index in range(1001))
        self.write_files({name: "class ExampleValue:\n    pass\n" for name in names})
        result = self.extract_project("python")
        assert len(result.extraction.files) == 1001
        assert tuple(result.extraction.files) == names
