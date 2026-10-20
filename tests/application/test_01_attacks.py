import hashlib
import json
import os
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from modwire.application import (
    ArchitectureError,
    CacheAccessError,
    CacheError,
    CacheOwnershipError,
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
    InitializationError,
    InvalidImplementationManifestError,
    InvalidInitializationTargetError,
    InvalidSourceRootError,
    ManifestFormat,
    ModwireError,
    SourceAccessError,
    SourceObservationInvalidatedError,
    UnknownFlowAnalyzerError,
    UnsupportedLanguageError,
    UnsupportedManifestFormatError,
    UnsupportedParserError,
)

from .base_test import ApplicationTestCase


class TestModwireApplicationAttacks(ApplicationTestCase):
    @pytest.mark.parametrize(
        ("error_type", "family"),
        (
            (ArchitectureError, ModwireError),
            (UnknownFlowAnalyzerError, ArchitectureError),
            (CacheError, ModwireError),
            (CacheOwnershipError, CacheError),
            (CacheAccessError, CacheError),
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
            (ImplementationManifestError, ModwireError),
            (UnsupportedManifestFormatError, ImplementationManifestError),
            (InvalidImplementationManifestError, ImplementationManifestError),
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

    def test_invalid_configuration_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self.application.configure({"shape": {"realms": [{"name": "", "match": "src"}]}})

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
