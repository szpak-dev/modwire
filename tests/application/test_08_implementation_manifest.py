import hashlib
import json
import shutil

import pytest

from modwire.application import (
    CodeMap,
    CodeValidationError,
    DigestAlgorithm,
    FactCapability,
    RelationshipFamily,
)

from ..support.code_map import CodeMapFactory
from ..support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from .base_test import ApplicationTestCase


class TestImplementationManifest(ApplicationTestCase):
    contract = PolyglotFixtureContract(ApplicationTestCase.repository)

    def test_public_code_map_rejects_a_non_value_symbol_kind_without_changing_valid_input(self) -> None:
        code_map = (
            CodeMapFactory()
            .queryable(
                {
                    "example.source": {
                        "values": [
                            CodeMapFactory().source_value(
                                "example_value",
                                declaration_kind="assignment",
                                scope="module",
                            )
                        ]
                    }
                },
                (),
            )
            .code_map
        )
        before = code_map.to_json()
        invalid = before.replace('"value_kind": "value_literal"', '"value_kind": "class"', 1)

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(invalid)

        assert raised.value.subject == "example_value"
        assert code_map.to_json() == before
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map, format)
        )
        assert tuple(item.kind for item in manifest.symbols) == ("value_literal",)

    def test_public_manifest_uses_one_authored_namespace_across_multiple_sources(self) -> None:
        namespace = {"kind": "namespace", "qualified_name": "Example.Shared"}
        code_map = (
            CodeMapFactory()
            .queryable(
                {
                    "example_first.source": {
                        "namespaces": [namespace],
                        "declarations": [
                            CodeMapFactory().source_class("ExampleFirst", line_count=1, methods=(), properties=())
                        ],
                    },
                    "example_second.source": {
                        "namespaces": [namespace],
                        "declarations": [
                            CodeMapFactory().source_class("ExampleSecond", line_count=1, methods=(), properties=())
                        ],
                    },
                },
                (),
            )
            .code_map
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map, format)
        )

        assert tuple(item.qualified_name for item in manifest.namespaces) == ("Example.Shared",)
        assert {item.qualified_name for item in manifest.symbols} == {
            "Example.Shared.ExampleFirst",
            "Example.Shared.ExampleSecond",
        }

    def test_every_matrix_manifest_scenario_has_exact_public_evidence_and_provenance(self) -> None:
        for language, scenario in self.contract.manifest_cases():
            root = self.contract.manifest_root(language, scenario)
            code_map = self.application.generate_map(language.value, str(root), self.scan_policy())
            formats = self.application.implementation_manifest_formats()
            document = self.application.implementation_manifest(code_map, formats[0])
            manifest = self.application.read_implementation_manifest(document)
            canonical = json.dumps(
                manifest.model_dump(mode="json"),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )

            assert tuple(format.id for format in formats) == ("canonical-json",), language.value
            assert manifest.schema_version == 10, language.value
            assert manifest.producer.extractor.language == language.value
            assert manifest.producer.extractor.version, language.value
            assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability), language.value
            assert {item.family for item in manifest.producer.relationship_capabilities} == set(RelationshipFamily), (
                language.value
            )
            assert manifest.source_manifest.policy == self.scan_policy(), language.value
            assert tuple(item.relative_path for item in manifest.source_manifest.sources) == (
                scenario.source.value.relative_to(scenario.name.value).as_posix(),
            )
            assert all(result.satisfied for result in self.contract.evaluate_manifest(manifest, scenario)), (
                f"{language.value}:{scenario.name.value}"
            )
            assert str(root) not in canonical
            assert all("annotation" not in item.model_dump() for item in manifest.attributes)
            assert "parameter_type" not in document.payload
            assert "return_type" not in document.payload
            assert "attribute_type" not in document.payload
            assert document.payload == canonical
            assert document.algorithm is DigestAlgorithm.SHA256
            assert document.digest == hashlib.sha256(canonical.encode()).hexdigest()
            assert document.digest == scenario.digest
            assert document.verify_digest()
            assert self.application.implementation_manifest(code_map, formats[0]) == document

    def test_every_matrix_manifest_transition_changes_each_declared_identity(self) -> None:
        scenarios = {(language, scenario.name): scenario for language, scenario in self.contract.manifest_cases()}
        for language, bundle, transition in self.contract.manifest_transition_cases():
            before_scenario = scenarios[(language, transition.before)]
            after_scenario = scenarios[(language, transition.after)]
            root = self.workspace / f"{language.value}_{transition.before.value}_{transition.after.value}"
            shutil.copytree(self.contract.manifest_root(language, before_scenario), root)
            format = self.application.implementation_manifest_formats()[0]
            before_document = self.application.implementation_manifest(
                self.application.generate_map(language.value, str(root), self.scan_policy()), format
            )
            before_source = before_scenario.source.value
            after_source = after_scenario.source.value
            shutil.copyfile(
                self.repository / bundle.contract.manifests.root.value / after_source,
                root / before_source.relative_to(transition.before.value),
            )
            after_document = self.application.implementation_manifest(
                self.application.generate_map(language.value, str(root), self.scan_policy()), format
            )
            before = self.application.read_implementation_manifest(before_document)
            after = self.application.read_implementation_manifest(after_document)

            observed_changes = {
                "source_identity": before.source_manifest.digest != after.source_manifest.digest,
                "implementation_identity": before_document.digest != after_document.digest,
            }
            assert all(observed_changes[change.value] for change in transition.changes), language.value
