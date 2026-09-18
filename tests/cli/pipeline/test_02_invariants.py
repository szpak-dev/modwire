import pytest

from .base_test import NativeExtractionTestCase


class TestNativeExtractionInvariants(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("language", "resolved", "external"), (("python", 7, 3), ("typescript", 5, 2), ("php", 6, 2))
    )
    def test_native_languages_preserve_dependency_resolution(self, language: str, resolved: int, external: int) -> None:
        result = self.fixture_map(language)
        assert result.tracked_dependency_edges().count() == resolved
        assert result.external_dependency_edges().count() == external
        assert result.code_map.extraction.files_excluded == 0
        assert result.code_map.extraction.directories_pruned == 1
        assert result.code_map.extraction.files_found == len(result.source_ids())

    @pytest.mark.parametrize("language", ("python", "typescript", "php"))
    def test_discovers_each_fixture_language(self, language: str) -> None:
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

    def test_typescript_tolerates_nonliteral_imports(self) -> None:
        self.write_files(
            {"example.ts": "import { example_value } from exampleModule;\nexport const example_result = 1;\n"}
        )
        result = self.extract_project("typescript")
        assert result.extraction.files["example.ts"].imports == []
        assert result.extraction.files["example.ts"].public_symbol_count == 1

    def test_php_tolerates_anonymous_class_construction(self) -> None:
        self.write_files(
            {
                "example.php": (
                    "<?php\nclass ExampleFactory {\n"
                    "    public function example_build(): object { return new class {}; }\n}\n"
                )
            }
        )
        result = self.extract_project("php")
        assert result.extraction.files["example.php"].classes[0].name == "ExampleFactory"
        assert result.extraction.files["example.php"].calls == []

    def test_large_source_input_keeps_every_file_and_identity(self) -> None:
        self.write_files({f"example_{index}.py": "class ExampleValue:\n    pass\n" for index in range(501)})
        result = self.extract_project("python")
        assert len(result.extraction.files) == 501
        assert set(result.extraction.files) == {f"example_{index}.py" for index in range(501)}
