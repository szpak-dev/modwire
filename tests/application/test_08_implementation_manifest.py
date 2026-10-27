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
    SourceCallResolution,
    SourceDependencyKind,
)

from ..support.code_map import CodeMapFactory
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from ..support.code_map_fixture.language_capability_matrix.row import LanguageCapabilityRow
from .base_test import ApplicationTestCase


class TestImplementationManifest(ApplicationTestCase):
    capability_matrix = LanguageCapabilityMatrixReader().read(
        ApplicationTestCase.repository / "language-capabilities.yaml"
    )

    def manifest_scenario_root(self, row: LanguageCapabilityRow, scenario: str) -> Path:
        return self.repository / row.fixtures.manifest_root / row.fixtures.manifest_scenario_root(scenario)

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
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_publishes_a_canonical_complete_provenance_bearing_manifest(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        root = self.manifest_scenario_root(row, "canonical")
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
        assert manifest.schema_version == 9
        assert manifest.producer.extractor.language == language
        assert manifest.producer.extractor.version
        assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
        assert {item.family for item in manifest.producer.relationship_capabilities} == set(RelationshipFamily)
        assert manifest.source_manifest.policy == self.scan_policy()
        assert tuple(item.relative_path for item in manifest.source_manifest.sources) == (
            str(row.fixtures.manifest_source("canonical").relative_to("canonical")),
        )
        assert str(root) not in canonical
        assert manifest.symbols
        assert manifest.callables
        assert manifest.declaration_relations
        assert manifest.dependencies
        assert document.payload == canonical
        assert document.algorithm is DigestAlgorithm.SHA256
        assert document.digest == hashlib.sha256(canonical.encode()).hexdigest()
        assert document.verify_digest()
        assert self.application.implementation_manifest(code_map, formats[0]) == document

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_preserves_two_distinct_observed_calls(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        code_map = self.application.generate_queryable_map(
            language,
            self.manifest_scenario_root(row, "calls"),
            self.scan_policy(),
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map.code_map, format)
        )
        calls = tuple(result.item for result in code_map.calls().all())

        assert len(calls) == len(manifest.calls) == 2
        assert tuple(item.ordinal for item in calls) == (1, 2)
        assert tuple(sorted(item.ordinal for item in manifest.calls)) == (1, 2)
        assert len({item.identity() for item in calls}) == 2
        assert len({item.target_name for item in calls}) == 1
        assert all(item.resolution is SourceCallResolution.RESOLVED for item in (*calls, *manifest.calls))
        assert all(item.target_callable_id is not None for item in (*calls, *manifest.calls))

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_truthfully_publishes_no_observed_calls(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        code_map = self.application.generate_queryable_map(
            language,
            self.manifest_scenario_root(row, "no_calls"),
            self.scan_policy(),
        )
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                code_map.code_map, self.application.implementation_manifest_formats()[0]
            )
        )
        member = next(
            coverage
            for coverage in code_map.code_map.producer.relationship_capabilities
            if coverage.family is RelationshipFamily.MEMBER
        )

        assert FactCapability.CALLS in member.evidence_requirements
        assert code_map.calls().all() == ()
        assert manifest.calls == ()

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_does_not_fabricate_runtime_or_generated_members(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map(
                    language,
                    self.manifest_scenario_root(row, "negative_members"),
                    self.scan_policy(),
                ),
                self.application.implementation_manifest_formats()[0],
            )
        )

        assert not any("runtime" in item.name.lower() for item in manifest.attributes)
        assert not any(
            "generated" in item.symbol_id.qualified_name.rsplit(".", 1)[-1].lower() for item in manifest.callables
        )

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_publishes_its_authored_dependency(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map(
                    language,
                    self.manifest_scenario_root(row, "dependencies"),
                    self.scan_policy(),
                ),
                self.application.implementation_manifest_formats()[0],
            )
        )

        assert len(manifest.dependencies) == 1
        assert manifest.dependencies[0].specifier
        assert manifest.dependencies[0].kind is SourceDependencyKind.IMPORTS

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_source_edit_changes_source_and_implementation_identity_for_each_language(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        root = self.workspace / f"{language}_source_edit"
        shutil.copytree(self.manifest_scenario_root(row, "source_edit_before"), root)
        format = self.application.implementation_manifest_formats()[0]
        before_document = self.application.implementation_manifest(
            self.application.generate_map(language, root, self.scan_policy()), format
        )
        before_source = row.fixtures.manifest_source("source_edit_before")
        after_source = row.fixtures.manifest_source("source_edit_after")
        shutil.copyfile(
            self.repository / row.fixtures.manifest_root / after_source,
            root / before_source.relative_to("source_edit_before"),
        )
        after_document = self.application.implementation_manifest(
            self.application.generate_map(language, root, self.scan_policy()), format
        )
        before = self.application.read_implementation_manifest(before_document)
        after = self.application.read_implementation_manifest(after_document)

        assert before.source_manifest.digest != after.source_manifest.digest
        assert before_document.digest != after_document.digest

    def test_matrix_languages_publish_one_manifest_vocabulary(self) -> None:
        format = self.application.implementation_manifest_formats()[0]
        manifests = {
            language: self.application.read_implementation_manifest(
                self.application.implementation_manifest(
                    self.application.generate_map(
                        language,
                        self.manifest_scenario_root(row, "canonical"),
                        self.scan_policy(),
                    ),
                    format,
                )
            )
            for language, row in self.capability_matrix.languages.items()
        }

        assert len({tuple(manifest.model_dump(mode="json")) for manifest in manifests.values()}) == 1

    def test_every_manifest_fixture_declared_by_the_matrix_is_executable(self) -> None:
        for language, row in self.capability_matrix.languages.items():
            for scenario in row.fixtures.manifest_sources:
                code_map = self.application.generate_map(
                    language,
                    self.manifest_scenario_root(row, scenario),
                    self.scan_policy(),
                )
                assert tuple(code_map.extraction.files) == (
                    str(row.fixtures.manifest_source(scenario).relative_to(scenario)),
                )
