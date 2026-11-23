import os
import shutil
from pathlib import Path

import pytest

from modwire.application import (
    DuplicateIdentityError,
    ExtractorError,
    ExtractorExecutionError,
    SourceParseError,
    UnsupportedLanguageError,
)

from ...support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ...support.code_map_fixture.language_capability_matrix.values.names.language_id import LanguageId
from .base_test import NativeExtractionTestCase


class TestNativeExtractionAttacks(NativeExtractionTestCase):
    @pytest.mark.parametrize("language", ("python", "typescript", "php", "java", "ruby"))
    def test_reports_native_parser_failure(self, language: str) -> None:
        fixture = self.repository / "tests/fixtures/extraction_lifecycle" / language / "invalid"
        source = next(fixture.iterdir())
        shutil.copyfile(source, self.workspace / source.name)
        with pytest.raises(SourceParseError) as raised:
            self.extract_project(language)
        assert raised.value.language == language
        assert raised.value.path.endswith(source.name)
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

    def test_missing_ruby_dependency_fails_and_recovers_with_real_runtime(self) -> None:
        root = self.repository / "tests/fixtures/extraction_lifecycle/ruby/valid"
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("RUBYLIB", str(self.repository / "tests/fixtures/runtime_environment"))
            environment.setenv("RUBYOPT", "--disable-gems -rno_library_paths")
            with pytest.raises(ExtractorExecutionError) as raised:
                self.application.generate_map("ruby", str(root), self.scan_policy())
        assert raised.value.language == "ruby"
        assert "cannot load such file -- prism" in raised.value.diagnostic
        recovered = self.application.generate_map("ruby", str(root), self.scan_policy())
        assert recovered.extraction.files["example.rb"].declarations[0].name == "ExampleValue"

    def test_incompatible_prism_fails_and_recovers_with_real_runtime(self) -> None:
        root = self.repository / "tests/fixtures/extraction_lifecycle/ruby/valid"
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("GEM_HOME", str(self.workspace / "gems"))
            environment.setenv("GEM_PATH", str(self.workspace / "gems"))
            environment.setenv("RUBYLIB", "")
            environment.setenv("RUBYOPT", "--disable-gems")
            with pytest.raises(ExtractorExecutionError) as raised:
                self.application.generate_map("ruby", str(root), self.scan_policy())
        assert raised.value.language == "ruby"
        assert "Prism 1.9.x is required." in raised.value.diagnostic
        recovered = self.application.generate_map("ruby", str(root), self.scan_policy())
        assert recovered.extraction.files["example.rb"].declarations[0].name == "ExampleValue"

    def test_incompatible_ruby_fails_before_loading_prism_and_recovers(self) -> None:
        root = self.repository / "tests/fixtures/extraction_lifecycle/ruby/valid"
        contract = PolyglotFixtureContract(self.repository)
        requirement = contract.matrix.languages[LanguageId("ruby")].contract.runtime
        assert "MODWIRE_TEST_REJECTED_RUBY" in os.environ, "Configure the rejected Ruby described in contributing."
        executable = Path(os.environ["MODWIRE_TEST_REJECTED_RUBY"])
        assert executable.is_absolute() and executable.is_file()
        rejected_bin = self.workspace / "rejected-runtime"
        rejected_bin.mkdir()
        (rejected_bin / requirement.runtime.value).symlink_to(executable)
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("PATH", str(rejected_bin) + os.pathsep + os.environ["PATH"])
            environment.setenv("RUBYOPT", "")
            contract.runtime.validate_version(str(executable), requirement, requirement.rejected_versions[0])
            with pytest.raises(ExtractorExecutionError) as raised:
                self.application.generate_map("ruby", str(root), self.scan_policy())
        assert raised.value.language == "ruby"
        assert "Ruby 4.0.x is required." in raised.value.diagnostic
        recovered = self.application.generate_map("ruby", str(root), self.scan_policy())
        assert recovered.extraction.files["example.rb"].declarations[0].name == "ExampleValue"

    def test_rejects_an_unsupported_language(self) -> None:
        with pytest.raises(UnsupportedLanguageError) as raised:
            self.extract_project("example_unknown")
        assert raised.value.language == "example_unknown"
        assert raised.value.supported_languages == self.application.extraction.supported_languages()

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
