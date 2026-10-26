import hashlib
import json
import os
import sys
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError
from ruamel.yaml.error import YAMLError

from modwire.application import (
    ArchitectureConfigError,
    ArchitectureConfigValidationError,
    ArchitectureConfigViolation,
    ArchitectureError,
    ArchitectureShapeError,
    ArchitectureShapeValidationError,
    CacheAccessError,
    CacheError,
    CacheOwnershipError,
    CacheValidationError,
    CodeError,
    CodeValidationError,
    CodeViolation,
    ConfigurationLoadError,
    DigestAlgorithm,
    DuplicateIdentityError,
    ExtractionError,
    ExtractorContractError,
    ExtractorContractViolation,
    ExtractorError,
    ExtractorExecutionError,
    ExtractorResourceError,
    ExtractorUnavailableError,
    ImplementationManifestDocument,
    ImplementationManifestError,
    ImplementationManifestValidationError,
    ImplementationManifestViolation,
    InitializationError,
    InvalidImplementationManifestError,
    InvalidInitializationTargetError,
    InvalidSourceRootError,
    ManifestFormat,
    ModwireError,
    PipelineError,
    PipelineValidationError,
    PipelineViolation,
    SourceAccessError,
    SourceCall,
    SourceObservationInvalidatedError,
    SourceParseError,
    UnknownFlowAnalyzerError,
    UnsupportedLanguageError,
    UnsupportedManifestFormatError,
    UnsupportedParserError,
)

from .base_test import ApplicationTestCase


class TestModwireApplicationAttacks(ApplicationTestCase):
    def call_manifest_document(self, *, two_calls: bool) -> ImplementationManifestDocument:
        body = "return example_second(example_first())" if two_calls else "return example_target()"
        declarations = (
            "def example_first():\n    return 1\n\ndef example_second(example_value):\n    return example_value\n\n"
            if two_calls
            else "def example_target():\n    return 1\n\n"
        )
        root = self.project({"src/example.py": f"{declarations}def example_caller():\n    {body}\n"})
        format = self.application.implementation_manifest_formats()[0]
        return self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()),
            format,
        )

    def tampered_document(
        self,
        document: ImplementationManifestDocument,
        mutate: Callable[[dict[str, Any]], None],
    ) -> ImplementationManifestDocument:
        payload = json.loads(document.payload)
        mutate(payload)
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return document.model_copy(
            update={
                "payload": serialized,
                "digest": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            }
        )

    @pytest.mark.parametrize("ordinal", (None, 0))
    def test_source_call_rejects_a_missing_or_non_positive_occurrence_ordinal(self, ordinal: int | None) -> None:
        document = self.call_manifest_document(two_calls=False)
        call = json.loads(document.payload)["calls"][0]
        if ordinal is None:
            del call["ordinal"]
        else:
            call["ordinal"] = ordinal

        with pytest.raises(ValidationError) as raised:
            SourceCall.model_validate(call)

        assert raised.value.errors()[0]["loc"] == ("ordinal",)

    @pytest.mark.parametrize(
        ("error_type", "family"),
        (
            (ArchitectureError, ModwireError),
            (UnknownFlowAnalyzerError, ArchitectureError),
            (ArchitectureConfigError, ModwireError),
            (ArchitectureConfigValidationError, ArchitectureConfigError),
            (ArchitectureShapeError, ModwireError),
            (ArchitectureShapeValidationError, ArchitectureShapeError),
            (CacheError, ModwireError),
            (CacheOwnershipError, CacheError),
            (CacheAccessError, CacheError),
            (CacheValidationError, CacheError),
            (CodeError, ModwireError),
            (CodeValidationError, CodeError),
            (PipelineError, ModwireError),
            (PipelineValidationError, PipelineError),
            (ConfigurationLoadError, PipelineError),
            (ExtractionError, ModwireError),
            (UnsupportedLanguageError, ExtractionError),
            (UnsupportedParserError, ExtractionError),
            (InvalidSourceRootError, ExtractionError),
            (SourceAccessError, ExtractionError),
            (SourceObservationInvalidatedError, ExtractionError),
            (DuplicateIdentityError, ExtractionError),
            (ExtractorError, ExtractionError),
            (ExtractorUnavailableError, ExtractorError),
            (ExtractorResourceError, ExtractorError),
            (ExtractorExecutionError, ExtractorError),
            (ExtractorContractError, ExtractorError),
            (SourceParseError, ExtractorError),
            (ImplementationManifestError, ModwireError),
            (UnsupportedManifestFormatError, ImplementationManifestError),
            (InvalidImplementationManifestError, ImplementationManifestError),
            (ImplementationManifestValidationError, ImplementationManifestError),
            (InitializationError, ModwireError),
            (InvalidInitializationTargetError, InitializationError),
        ),
    )
    def test_public_failure_types_follow_the_documented_taxonomy(
        self,
        error_type: type[ModwireError],
        family: type[BaseException],
    ) -> None:
        assert issubclass(error_type, family)
        assert issubclass(error_type, ModwireError)
        assert not issubclass(error_type, (RuntimeError, ValueError))

    def test_invalid_source_root_reports_the_rejected_public_input(self) -> None:
        missing = self.workspace / "example-missing"

        with pytest.raises(InvalidSourceRootError) as raised:
            self.application.generate_map("python", str(missing), self.scan_policy())

        assert raised.value.root == str(missing)

    @pytest.mark.parametrize(
        ("language", "path", "source", "executable"),
        (
            ("typescript", "src/example.ts", "export const exampleValue = 1;\n", "node"),
            ("java", "src/ExampleValue.java", "public class ExampleValue {}\n", "java"),
        ),
    )
    def test_unavailable_extractor_reports_the_runtime_contract(
        self, language: str, path: str, source: str, executable: str
    ) -> None:
        root = self.project({path: source})

        result = self.failure_consumer(root, language, {**os.environ, "PATH": ""})

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {
            "executable": executable,
            "language": language,
            "type": "ExtractorUnavailableError",
        }

    def test_invalid_extractor_output_reports_a_contract_violation(self) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "print('example 1' if '--version' in sys.argv else 'example-invalid-output')\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        result = self.failure_consumer(root, "typescript", {**os.environ, "PATH": str(runtime_directory)})

        assert result.returncode == 0, result.stderr
        failure = json.loads(result.stdout)
        assert failure["type"] == "ExtractorContractError"
        assert failure["language"] == "typescript"
        assert failure["violation"] == ExtractorContractViolation.INVALID_OUTPUT
        assert failure["cause"] == ValidationError.__name__

    @pytest.mark.parametrize(
        "document",
        (
            "{}",
            '["source_parse"]',
            '{"language":"typescript","path":"example.ts","line":1,"column":1,"diagnostic":"invalid"}',
            '{"code":"source_parse","language":"typescript","path":"example.ts","line":"1","column":1,"diagnostic":"invalid"}',
            '{"code":"source_parse","language":"typescript","path":"example.ts","line":true,"column":1,"diagnostic":"invalid"}',
            '{"code":"source_parse","language":"typescript","path":"example.ts","line":null,"column":1,"diagnostic":"invalid"}',
            '{"code":"source_parse","language":"typescript","path":"example.ts","line":0,"column":1,"diagnostic":"invalid"}',
            '{"code":"source_parse","language":"typescript","path":"example.ts","line":1,"column":1,"diagnostic":"invalid","extra":"forbidden"}',
        ),
    )
    def test_malformed_typed_extractor_failure_reports_a_contract_violation(self, document: str) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-malformed-failure-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('example 1')\n"
            "else:\n"
            f"    print('modwire-error:' + {document!r}, file=sys.stderr)\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("PATH", str(runtime_directory))
            with pytest.raises(ExtractorContractError) as raised:
                self.application.generate_map("typescript", root, self.scan_policy())

        assert raised.value.language == "typescript"
        assert raised.value.violation is ExtractorContractViolation.INVALID_OUTPUT
        assert isinstance(raised.value.__cause__, ValidationError)

    def test_extractor_failure_language_must_match_its_runtime(self) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-wrong-language-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        document = (
            '{"code":"source_parse","language":"python","path":"example.ts","line":1,"column":1,"diagnostic":"invalid"}'
        )
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('example 1')\n"
            "else:\n"
            f"    print('modwire-error:' + {document!r}, file=sys.stderr)\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("PATH", str(runtime_directory))
            with pytest.raises(ExtractorContractError) as raised:
                self.application.generate_map("typescript", root, self.scan_policy())

        assert raised.value.violation is ExtractorContractViolation.INVALID_OUTPUT
        assert raised.value.diagnostic == "extractor failure document language does not match its runtime"
        assert isinstance(raised.value.__cause__, ExtractorExecutionError)

    def test_unmarked_extractor_failure_remains_an_execution_failure(self) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-unmarked-failure-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('example 1')\n"
            "else:\n"
            "    print('unmarked failure', file=sys.stderr)\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("PATH", str(runtime_directory))
            with pytest.raises(ExtractorExecutionError) as raised:
                self.application.generate_map("typescript", root, self.scan_policy())

        assert raised.value.language == "typescript"
        assert raised.value.exit_code == 1

    def test_multiple_typed_extractor_failures_report_a_contract_violation(self) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-multiple-failure-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('example 1')\n"
            "else:\n"
            "    print('modwire-error:{}', file=sys.stderr)\n"
            "    print('modwire-error:{}', file=sys.stderr)\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("PATH", str(runtime_directory))
            with pytest.raises(ExtractorContractError) as raised:
                self.application.generate_map("typescript", root, self.scan_policy())

        assert raised.value.language == "typescript"
        assert raised.value.violation is ExtractorContractViolation.INVALID_OUTPUT
        assert raised.value.diagnostic == "extractor emitted multiple failure documents"
        assert isinstance(raised.value.__cause__, ExtractorExecutionError)

    def test_duplicate_extractor_output_identities_report_a_contract_violation(self) -> None:
        root = self.project({"src/example.ts": "export const exampleValue = 1;\n"})
        runtime_directory = self.workspace / "example-duplicate-runtime"
        runtime_directory.mkdir()
        runtime = runtime_directory / "node"
        runtime.write_text(
            f"#!{sys.executable}\n"
            "import json\n"
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('example 1')\n"
            "else:\n"
            "    for source_id in json.load(sys.stdin):\n"
            "        document = json.dumps([source_id, {}])\n"
            "        print(document)\n"
            "        print(document)\n",
            encoding="utf-8",
        )
        runtime.chmod(0o755)

        result = self.failure_consumer(root, "typescript", {**os.environ, "PATH": str(runtime_directory)})

        assert result.returncode == 0, result.stderr
        failure = json.loads(result.stdout)
        assert failure["type"] == "ExtractorContractError"
        assert failure["language"] == "typescript"
        assert failure["violation"] == ExtractorContractViolation.DUPLICATE_SOURCE_IDENTITY
        assert failure["missing_source_ids"] == []
        assert failure["unexpected_source_ids"] == []
        assert failure["duplicate_source_ids"] == ["src/example.ts"]

    def test_cache_access_reports_the_public_cache_path(self) -> None:
        cache_file = self.workspace / "example-cache-file"
        cache_file.write_text("example", encoding="utf-8")
        options = self.cache_options("example-cache-access").model_copy(update={"directory": str(cache_file)})

        with pytest.raises(CacheAccessError) as raised:
            self.application.clear_cache(options)

        assert raised.value.path == str(cache_file)
        assert isinstance(raised.value.__cause__, OSError)

    def test_unsupported_manifest_format_reports_registered_formats(self) -> None:
        root = self.project({"src/example.py": "example_value = 1\n"})
        format = ManifestFormat(id="example-unsupported", media_type="application/example")
        code_map = self.application.generate_map("python", root, self.scan_policy())

        with pytest.raises(UnsupportedManifestFormatError) as raised:
            self.application.implementation_manifest(code_map, format)

        assert raised.value.format == format
        assert tuple(item.id for item in raised.value.supported_formats) == ("canonical-json",)

    @pytest.mark.parametrize(
        "path",
        (
            ("source_manifest", "digest_algorithm"),
            ("symbols", 0, "kind"),
            ("symbols", 0, "visibility"),
            ("callables", 0, "callable_kind"),
            ("parameters", 0, "kind"),
            ("annotations", 0, "role"),
            ("dependencies", 0, "target_kind"),
            ("dependencies", 0, "resolution"),
        ),
    )
    def test_manifest_rejects_unknown_closed_vocabulary_values(self, path: tuple[str | int, ...]) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "from example_external import ExampleExternal\n\n"
                    "class ExampleValue:\n"
                    "    example_name: str\n\n"
                    "    @example_decorator\n"
                    "    def execute(self, example_input: int = 1) -> str:\n"
                    "        return str(example_input)\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()), format
        )
        payload: dict[str, Any] = json.loads(document.payload)
        target: Any = payload
        for segment in path[:-1]:
            target = target[segment]
        target[path[-1]] = "example_invalid"
        invalid_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        invalid_document = ImplementationManifestDocument(
            format=format,
            payload=invalid_payload,
            algorithm=DigestAlgorithm.SHA256,
            digest=hashlib.sha256(invalid_payload.encode("utf-8")).hexdigest(),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid_document)
        assert raised.value.format_id == format.id

    def test_manifest_without_assigned_value_evidence_is_rejected(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    example_value: int\n"})
        format = self.application.implementation_manifest_formats()[0]
        document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()), format
        )
        payload = json.loads(document.payload)
        payload["attributes"][0]["assigned_values"] = []
        invalid_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        invalid_document = ImplementationManifestDocument(
            format=format,
            payload=invalid_payload,
            algorithm=DigestAlgorithm.SHA256,
            digest=hashlib.sha256(invalid_payload.encode("utf-8")).hexdigest(),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid_document)
        assert raised.value.format_id == format.id

    @pytest.mark.parametrize(
        ("field", "subject"),
        (
            ("source_callable_id", "call source callables"),
            ("target_callable_id", "call target callables"),
        ),
    )
    def test_manifest_rejects_calls_with_unknown_callable_references(self, field: str, subject: str) -> None:
        document = self.call_manifest_document(two_calls=False)
        invalid = self.tampered_document(
            document,
            lambda payload: payload["calls"][0][field].__setitem__("qualified_name", "example_missing_callable"),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.UNKNOWN_REFERENCE
        assert cause.subject == subject

    def test_manifest_rejects_a_call_from_an_unknown_source(self) -> None:
        document = self.call_manifest_document(two_calls=False)
        invalid = self.tampered_document(
            document,
            lambda payload: payload["calls"][0].__setitem__("source_id", "src/example-missing.py"),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.UNKNOWN_REFERENCE
        assert cause.subject == "call sources"

    def test_manifest_rejects_a_call_target_that_contradicts_its_resolution(self) -> None:
        document = self.call_manifest_document(two_calls=False)
        invalid = self.tampered_document(
            document,
            lambda payload: payload["calls"][0].__setitem__("resolution", "external"),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.INCONSISTENT_CALL
        assert cause.subject == "call target resolutions"

    def test_manifest_rejects_a_call_owned_by_another_source_callable(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "def example_target():\n    return 1\n\ndef example_caller():\n    return example_target()\n"
                ),
                "src/other.py": "def other_callable():\n    return 2\n",
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()),
            format,
        )
        invalid = self.tampered_document(
            document,
            lambda payload: payload["calls"][0].__setitem__(
                "source_callable_id",
                next(
                    item["symbol_id"]
                    for item in payload["callables"]
                    if item["symbol_id"]["qualified_name"] == "other_callable"
                ),
            ),
        )

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.INCONSISTENT_CALL_SOURCE
        assert cause.subject == "call source ownership"

    def test_manifest_rejects_non_canonical_call_order(self) -> None:
        document = self.call_manifest_document(two_calls=True)
        invalid = self.tampered_document(document, lambda payload: payload["calls"].reverse())

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.NON_CANONICAL_ORDER
        assert cause.subject == "calls"

    def test_manifest_rejects_duplicate_call_facts(self) -> None:
        document = self.call_manifest_document(two_calls=False)
        invalid = self.tampered_document(document, lambda payload: payload["calls"].append(payload["calls"][0]))

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.DUPLICATE_FACT
        assert cause.subject == "calls"

    def test_manifest_rejects_duplicate_call_occurrence_identities(self) -> None:
        document = self.call_manifest_document(two_calls=False)

        def repeat_identity_with_different_evidence(payload: dict[str, Any]) -> None:
            repeated = {**payload["calls"][0], "line": payload["calls"][0]["line"] + 1}
            payload["calls"].append(repeated)

        invalid = self.tampered_document(document, repeat_identity_with_different_evidence)

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, ImplementationManifestValidationError)
        assert cause.violation is ImplementationManifestViolation.DUPLICATE_IDENTITY
        assert cause.subject == "calls"

    def test_manifest_translates_nested_code_contract_failures(self) -> None:
        document = self.call_manifest_document(two_calls=False)

        def remove_relationship_evidence(payload: dict[str, Any]) -> None:
            member = next(
                coverage
                for coverage in payload["producer"]["relationship_capabilities"]
                if coverage["family"] == "member"
            )
            member["evidence_requirements"] = []

        invalid = self.tampered_document(document, remove_relationship_evidence)

        with pytest.raises(InvalidImplementationManifestError) as raised:
            self.application.read_implementation_manifest(invalid)

        cause = raised.value.__cause__
        assert isinstance(cause, CodeValidationError)
        assert cause.violation is CodeViolation.NON_CANONICAL_RELATIONSHIP_EVIDENCE
        assert cause.subject == "member"

    def test_invalid_python_syntax_reports_the_source_location_and_parser_cause(self) -> None:
        root = self.project({"src/example.py": "def example_value(\n"})

        with pytest.raises(SourceParseError) as raised:
            self.application.generate_map("python", root, self.scan_policy())

        assert raised.value.language == "python"
        assert raised.value.path.endswith("src/example.py")
        assert raised.value.line == 1
        assert raised.value.column > 0
        assert raised.value.diagnostic
        assert isinstance(raised.value.__cause__, ExtractorExecutionError)

    def test_missing_configuration_reports_the_public_path_and_access_cause(self) -> None:
        dot_dir = self.workspace / "example-missing-configuration"
        dot_dir.mkdir()

        with pytest.raises(ConfigurationLoadError) as raised:
            self.application.load_configuration(str(dot_dir))

        assert raised.value.violation is PipelineViolation.CONFIGURATION_ACCESS_FAILED
        assert raised.value.subject == str(dot_dir / "architecture.yaml")
        assert isinstance(raised.value.__cause__, OSError)

    def test_malformed_configuration_reports_the_public_path_and_parser_cause(self) -> None:
        dot_dir = self.workspace / "example-malformed-configuration"
        dot_dir.mkdir()
        configuration = dot_dir / "architecture.yaml"
        configuration.write_text("shape: [\n", encoding="utf-8")

        with pytest.raises(ConfigurationLoadError) as raised:
            self.application.load_configuration(str(dot_dir))

        assert raised.value.violation is PipelineViolation.CONFIGURATION_PARSE_FAILED
        assert raised.value.subject == str(configuration)
        assert isinstance(raised.value.__cause__, YAMLError)

    def test_invalid_configuration_file_reports_a_domain_validation_failure(self) -> None:
        dot_dir = self.workspace / "example-invalid-configuration"
        dot_dir.mkdir()
        configuration = dot_dir / "architecture.yaml"
        configuration.write_text("shape:\n  realms: []\n", encoding="utf-8")

        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.load_configuration(str(dot_dir))

        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert raised.value.subject == str(configuration)
        assert isinstance(raised.value.__cause__, ValidationError)

    def test_invalid_configuration_is_rejected(self) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure({"shape": {"realms": [{"name": "", "match": "src"}]}})

        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert raised.value.subject == "architecture configuration"
        assert isinstance(raised.value.__cause__, ValidationError)

    def test_configuration_does_not_leak_between_calls(self) -> None:
        code_map = self.application.generate_queryable_map(
            "python",
            self.project({"src/example.py": "def example_function():\n    pass\n"}),
            self.scan_policy(),
        )
        strict = self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
        permissive = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "src", "shape": {"max_functions_per_file": 1}}]}}
        )
        strict_reports = self.application.analyze(code_map, strict)
        permissive_reports = self.application.analyze(code_map, permissive)
        assert next(item for item in strict_reports if item.metadata.id == "architecture.violations.shape").violations
        assert not next(
            item for item in permissive_reports if item.metadata.id == "architecture.violations.shape"
        ).violations
        assert self.application.analyze(code_map, strict) == strict_reports
