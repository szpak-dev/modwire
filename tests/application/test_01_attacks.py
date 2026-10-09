import hashlib
import json
from typing import Any

import pytest
from pydantic import ValidationError

from modwire.application import DigestAlgorithm, ImplementationManifestDocument

from .base_test import ApplicationTestCase


class TestModwireApplicationAttacks(ApplicationTestCase):
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

        with pytest.raises(ValidationError):
            self.application.read_implementation_manifest(invalid_document)

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

        with pytest.raises(ValidationError):
            self.application.read_implementation_manifest(invalid_document)

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
