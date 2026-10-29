import hashlib
import json
import shutil
from pathlib import Path

import pytest

from modwire.application import (
    CodeMap,
    CodeValidationError,
    DigestAlgorithm,
    FactCapability,
    RelationshipFamily,
)

from ..support.code_map import CodeMapFactory
from ..support.code_map_fixture.language_capability_matrix.contract import LanguageCapabilityRow
from ..support.code_map_fixture.language_capability_matrix.manifests.coverage import (
    ManifestEvidenceExpectation,
    ManifestTransitionExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from ..support.code_map_fixture.manifest_evidence import FixtureManifestEvidence
from .base_test import ApplicationTestCase


class TestImplementationManifest(ApplicationTestCase):
    capability_matrix = LanguageCapabilityMatrixReader().read(
        ApplicationTestCase.repository / "language-capabilities.yaml"
    )

    def manifest_scenario_root(self, row: LanguageCapabilityRow, scenario: str) -> Path:
        source = row.fixtures.manifests.sources[scenario].value
        return self.repository / row.fixtures.manifests.root.value / source.parents[1]

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

    @pytest.mark.parametrize(
        ("language", "scenario", "expectation"),
        capability_matrix.manifest_cases(),
        ids=(
            f"{language}-{scenario}"
            for language, scenario, expectation in capability_matrix.manifest_cases()
        ),
    )
    def test_every_matrix_manifest_scenario_has_exact_public_evidence_and_provenance(
        self,
        language: str,
        scenario: str,
        expectation: ManifestEvidenceExpectation,
    ) -> None:
        row = self.capability_matrix.languages[language]
        root = self.manifest_scenario_root(row, scenario)
        code_map = self.application.generate_map(language, root, self.scan_policy())
        formats = self.application.implementation_manifest_formats()
        document = self.application.implementation_manifest(code_map, formats[0])
        manifest = self.application.read_implementation_manifest(document)
        canonical = json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        assert tuple(format.id for format in formats) == ("canonical-json",)
        assert manifest.schema_version == 10
        assert manifest.producer.extractor.language == language
        assert manifest.producer.extractor.version
        assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
        assert {item.family for item in manifest.producer.relationship_capabilities} == set(RelationshipFamily)
        assert manifest.source_manifest.policy == self.scan_policy()
        assert tuple(item.relative_path for item in manifest.source_manifest.sources) == (
            str(row.fixtures.manifests.sources[scenario].value.relative_to(scenario)),
        )
        assert str(root) not in canonical
        assert FixtureManifestEvidence().observe(manifest, expectation.source) == expectation
        assert all("annotation" not in item.model_dump() for item in manifest.attributes)
        assert "parameter_type" not in document.payload
        assert "return_type" not in document.payload
        assert "attribute_type" not in document.payload
        assert document.payload == canonical
        assert document.algorithm is DigestAlgorithm.SHA256
        assert document.digest == hashlib.sha256(canonical.encode()).hexdigest()
        assert document.verify_digest()
        assert self.application.implementation_manifest(code_map, formats[0]) == document

    @pytest.mark.parametrize(
        ("language", "row", "transition"),
        capability_matrix.manifest_transition_cases(),
    )
    def test_matrix_manifest_transition_changes_source_and_implementation_identity(
        self,
        language: str,
        row: LanguageCapabilityRow,
        transition: ManifestTransitionExpectation,
    ) -> None:
        root = self.workspace / f"{language}_{transition.before}_{transition.after}"
        shutil.copytree(self.manifest_scenario_root(row, transition.before), root)
        format = self.application.implementation_manifest_formats()[0]
        before_document = self.application.implementation_manifest(
            self.application.generate_map(language, root, self.scan_policy()), format
        )
        before_source = row.fixtures.manifests.sources[transition.before].value
        after_source = row.fixtures.manifests.sources[transition.after].value
        shutil.copyfile(
            self.repository / row.fixtures.manifests.root.value / after_source,
            root / before_source.relative_to(transition.before),
        )
        after_document = self.application.implementation_manifest(
            self.application.generate_map(language, root, self.scan_policy()), format
        )
        before = self.application.read_implementation_manifest(before_document)
        after = self.application.read_implementation_manifest(after_document)

        assert before.source_manifest.digest != after.source_manifest.digest
        assert before_document.digest != after_document.digest
