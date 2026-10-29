import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    FactCapability,
    RelationshipFamily,
)

from ..support.code_map_fixture.capability_evidence import FixtureCapabilityEvidence
from ..support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ..support.code_map_fixture.fixture_contract_error import FixtureContractError
from ..support.code_map_fixture.language_capability_matrix.capabilities.coverage import (
    CapabilityExpectation,
    ParameterKindExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.capabilities.limitations import (
    AnnotationLimitationExpectation,
    AssignedValueLimitationExpectation,
    AttributeLimitationExpectation,
    CallableLimitationExpectation,
    CallLimitationExpectation,
    CompositionLimitationExpectation,
    DependencyLimitationExpectation,
    ModifierLimitationExpectation,
    NamespaceLimitationExpectation,
    ParameterLimitationExpectation,
    SpanLimitationExpectation,
    SymbolLimitationExpectation,
    TypeReferenceLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.contract import (
    LanguageCapabilityMatrix,
    LanguageCapabilityRow,
    LimitationScenarioExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from ..support.code_map_fixture.language_capability_matrix.relationships.coverage import RelationshipExpectation
from ..support.code_map_fixture.language_capability_matrix.relationships.limitations import (
    DeclarationRelationshipLimitationExpectation,
    DependencyRelationshipLimitationExpectation,
    MemberRelationshipLimitationExpectation,
)
from ..support.code_map_fixture.projector import FixtureCodeMapProjector
from .base_test import ApplicationTestCase


class TestPolyglotCodeMapContract(ApplicationTestCase):
    capability_matrix = LanguageCapabilityMatrixReader().read(
        ApplicationTestCase.repository / "language-capabilities.yaml"
    )

    def capability_gap_root(self, language: str) -> Path:
        return self.repository / self.capability_matrix.languages[language].fixtures.capability_gaps.root.value

    def type_reference_root(self, language: str) -> Path:
        return self.repository / self.capability_matrix.languages[language].fixtures.type_references.root.value

    def scenario_source(self, scenario: LimitationScenarioExpectation) -> Path:
        return self.repository / scenario.source

    def test_missing_language_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        expected = tuple(sorted(self.capability_matrix.languages))
        row = next(iter(self.capability_matrix.languages.values()))
        root = (self.repository / row.fixtures.reference.root.value).parent

        with pytest.raises(FixtureContractError, match="language inventory mismatch"):
            contract.validate_language_inventory(root, expected[1:])

        contract.validate_language_inventory(root, expected)

    def test_extra_language_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        expected = tuple(sorted(self.capability_matrix.languages))
        row = next(iter(self.capability_matrix.languages.values()))
        root = (self.repository / row.fixtures.reference.root.value).parent

        with pytest.raises(FixtureContractError, match="language inventory mismatch"):
            contract.validate_language_inventory(root, (*expected, "attack"))

        contract.validate_language_inventory(root, expected)

    def test_missing_source_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        row = next(iter(self.capability_matrix.languages.values()))
        root = self.repository / row.fixtures.reference.root.value
        expected = contract.source_paths(root)

        with pytest.raises(FixtureContractError, match="source inventory mismatch"):
            contract.validate_source_inventory(root, expected[1:])

        contract.validate_source_inventory(root, expected)

    def test_duplicate_scenario_metadata_attack_is_rejected(self) -> None:
        language, scenario = self.capability_matrix.scenario_cases()[0]
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["scenarios"].append(scenario.model_dump(mode="json"))

        with pytest.raises(ValidationError, match="duplicate scenario metadata"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_duplicate_parameter_kind_vocabulary_attack_is_rejected(self) -> None:
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["index"]["parameter_kinds"].append(attacked["index"]["parameter_kinds"][0])

        with pytest.raises(ValidationError, match="parameter-kind vocabulary contains duplicates"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_unobserved_parameter_kind_vocabulary_attack_is_rejected(self) -> None:
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["index"]["parameter_kinds"].append("example_unobserved")
        for row in attacked["languages"].values():
            row["parameter_kinds"]["not_applicable"].append("example_unobserved")

        with pytest.raises(
            ValidationError,
            match="parameter-kind vocabulary contains a kind absent from every language",
        ):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_unknown_matrix_schema_version_attack_is_rejected(self) -> None:
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["index"]["schema_version"] = 2

        with pytest.raises(ValidationError, match="literal_error"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_duplicate_language_document_path_attack_is_rejected(self) -> None:
        attacked = self.capability_matrix.model_dump(mode="json")
        paths = tuple(attacked["index"]["languages"].values())
        attacked["index"]["languages"]["ruby"] = paths[0]

        with pytest.raises(ValidationError, match="language document paths contain duplicates"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_deep_language_document_path_attack_is_rejected(self) -> None:
        attacked = self.capability_matrix.model_dump(mode="json")
        for language in attacked["index"]["languages"]:
            attacked["index"]["languages"][language] = f"nested/languages/{language}.yaml"

        with pytest.raises(ValidationError, match="language documents must share one nested directory"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_language_document_identity_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["language"] = "example_language"

        with pytest.raises(ValidationError, match=f"{language} document declares language example_language"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_missing_language_document_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        index_path = self.workspace / "language-capabilities.yaml"
        document_root = self.workspace / "language-capabilities"
        shutil.copyfile(self.repository / "language-capabilities.yaml", index_path)
        shutil.copytree(self.repository / "language-capabilities", document_root)
        missing = document_root / "ruby.yaml"
        missing.unlink()

        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            LanguageCapabilityMatrixReader().read(index_path)

        shutil.copyfile(self.repository / "language-capabilities/ruby.yaml", missing)
        LanguageCapabilityMatrixReader().read(index_path)

    def test_missing_language_document_directory_attack_is_rejected_before_recovery(self) -> None:
        index_path = self.workspace / "language-capabilities.yaml"
        document_root = self.workspace / "language-capabilities"
        shutil.copyfile(self.repository / "language-capabilities.yaml", index_path)

        with pytest.raises(FixtureContractError, match="language document directory is missing"):
            LanguageCapabilityMatrixReader().read(index_path)

        shutil.copytree(self.repository / "language-capabilities", document_root)
        LanguageCapabilityMatrixReader().read(index_path)

    def test_extra_language_document_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        index_path = self.workspace / "language-capabilities.yaml"
        document_root = self.workspace / "language-capabilities"
        shutil.copyfile(self.repository / "language-capabilities.yaml", index_path)
        shutil.copytree(self.repository / "language-capabilities", document_root)
        extra = document_root / "example.yaml"
        extra.write_text("language: example\n", encoding="utf-8")

        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            LanguageCapabilityMatrixReader().read(index_path)

        extra.unlink()
        LanguageCapabilityMatrixReader().read(index_path)

    def test_non_file_language_document_attack_is_rejected_before_recovery(self) -> None:
        index_path = self.workspace / "language-capabilities.yaml"
        document_root = self.workspace / "language-capabilities"
        shutil.copyfile(self.repository / "language-capabilities.yaml", index_path)
        shutil.copytree(self.repository / "language-capabilities", document_root)
        relative_document = next(iter(self.capability_matrix.index.languages.values()))
        attacked_document = self.workspace / relative_document.value
        attacked_document.unlink()
        attacked_document.mkdir()

        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            LanguageCapabilityMatrixReader().read(index_path)

        attacked_document.rmdir()
        shutil.copyfile(self.repository / relative_document.value, attacked_document)
        LanguageCapabilityMatrixReader().read(index_path)

    def test_extra_nested_matrix_field_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["fixtures"]["reference"]["attack"] = True

        with pytest.raises(ValidationError, match="extra_forbidden"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_parsed_nested_matrix_model_reassignment_attack_is_rejected(self) -> None:
        fixtures = next(iter(self.capability_matrix.languages.values())).fixtures
        suffixes = fixtures.source_suffixes

        with pytest.raises(ValidationError, match="frozen_instance"):
            fixtures.source_suffixes = ()

        assert fixtures.source_suffixes == suffixes

    def test_limitation_detached_from_its_contract_cell_attack_is_rejected(self) -> None:
        language, row = next(iter(self.capability_matrix.languages.items()))
        capability = next(
            capability for capability, expectation in row.capabilities.items() if expectation.limitation_scenarios
        )
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["capabilities"][capability.value]["limitation_scenarios"] = [
            "detached-scenario"
        ]

        with pytest.raises(ValidationError, match="limitations are not owned by that capability"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_non_source_manifest_inventory_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["fixtures"]["manifests"]["sources"]["canonical"] = (
            "canonical/src/example.unsupported"
        )

        with pytest.raises(ValidationError, match="source suffix inventory differs"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_manifest_source_outside_its_named_scenario_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["fixtures"]["manifests"]["sources"]["canonical"] = attacked["languages"][
            language
        ]["fixtures"]["manifests"]["sources"]["calls"]

        with pytest.raises(ValidationError, match="manifest source is outside its named scenario"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_every_declared_source_suffix_exactly_covers_every_fixture_source(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        for row in self.capability_matrix.languages.values():
            fixtures = (
                row.fixtures.reference,
                row.fixtures.language_extensions,
                row.fixtures.capability_gaps,
                row.fixtures.parameter_kinds,
            )
            for fixture in fixtures:
                contract.validate_source_set(fixture)
                contract.validate_source_suffixes(fixture, row.fixtures.source_suffixes)
            assert {source.value.suffix for fixture in fixtures for source in fixture.sources} == {
                suffix.value for suffix in row.fixtures.source_suffixes
            }

    def test_capability_matrix_has_the_exact_supported_language_inventory(self) -> None:
        assert tuple(self.capability_matrix.languages) == self.application.supported_languages()

    def test_capability_matrix_covers_every_contract_cell(self) -> None:
        assert all(
            tuple(row.capabilities) == tuple(FactCapability) for row in self.capability_matrix.languages.values()
        )
        assert all(
            tuple(row.relationships) == tuple(RelationshipFamily) for row in self.capability_matrix.languages.values()
        )

    def test_limitation_fixture_inventory_is_driven_by_scenario_metadata(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        fixture_root = self.capability_gap_root(next(iter(self.capability_matrix.languages))).parent
        expected_languages = tuple(
            sorted(language for language, row in self.capability_matrix.languages.items() if row.scenarios)
        )

        contract.validate_language_inventory(fixture_root, expected_languages)
        for language, row in self.capability_matrix.languages.items():
            expected_sources = tuple(
                sorted(
                    {
                        Path(scenario.source).relative_to(row.fixtures.capability_gaps.root.value).as_posix()
                        for scenario in row.scenarios
                        if Path(scenario.source).is_relative_to(row.fixtures.capability_gaps.root.value)
                    }
                )
            )
            contract.validate_source_inventory(fixture_root / language, expected_sources)

    def test_implementation_manifest_fixture_inventory_covers_every_matrix_language(self) -> None:
        root = self.repository / "tests/fixtures/implementation_manifest"
        contract = PolyglotFixtureContract(self.repository)

        contract.validate_language_inventory(root, tuple(sorted(self.capability_matrix.languages)))
        for language, row in self.capability_matrix.languages.items():
            contract.validate_source_inventory(
                self.repository / row.fixtures.manifests.root.value,
                tuple(sorted(source.value.as_posix() for source in row.fixtures.manifests.sources.values())),
            )

    def test_type_reference_fixture_inventory_is_exactly_matrix_driven(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        for language, row in self.capability_matrix.languages.items():
            root = self.type_reference_root(language)
            expected = tuple(
                sorted(
                    (
                        row.fixtures.type_references.cases.value.as_posix(),
                        row.fixtures.type_references.empty.value.as_posix(),
                    )
                )
            )
            contract.validate_source_inventory(root, expected)

    def test_parameter_kind_fixture_inventory_is_exactly_matrix_driven(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        for row in self.capability_matrix.languages.values():
            contract.validate_source_inventory(
                self.repository / row.fixtures.parameter_kinds.root.value,
                tuple(source.value.as_posix() for source in row.fixtures.parameter_kinds.sources),
            )

    @pytest.mark.parametrize(
        ("language", "scenario"),
        capability_matrix.scenario_cases(),
        ids=[f"{language}-{scenario.scenario}" for language, scenario in capability_matrix.scenario_cases()],
    )
    def test_scenario_metadata_names_real_authored_syntax(
        self,
        language: str,
        scenario: LimitationScenarioExpectation,
    ) -> None:
        source = self.scenario_source(scenario).read_text(encoding="utf-8")

        assert all(authored_syntax in source for authored_syntax in scenario.authored_syntax)

    def test_reference_projects_have_the_exact_matrix_driven_source_inventory(self) -> None:
        contract = PolyglotFixtureContract(self.repository)
        master = CodeMap.model_validate_json(
            (self.repository / self.capability_matrix.reference_code_map).read_text(encoding="utf-8")
        )
        for row in self.capability_matrix.languages.values():
            assert master.extraction.files
            contract.validate_source_inventory(
                self.repository / row.fixtures.reference.root.value,
                tuple(source.value.as_posix() for source in row.fixtures.reference.sources),
            )

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_each_language_exactly_projects_the_reference_code_map(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        expected = CodeMap.model_validate_json(
            (self.repository / self.capability_matrix.reference_code_map).read_text(encoding="utf-8")
        )
        actual = self.application.generate_map(
            language,
            self.repository / row.fixtures.reference.root.value,
            self.configured_scan_policy(("ignored/**",), False),
        )

        assert FixtureCodeMapProjector().project(actual, row.projection, expected) == expected

    @pytest.mark.parametrize(
        ("language", "capability", "expectation"),
        capability_matrix.capability_cases(),
        ids=[
            f"{language}-{capability.value}"
            for language, capability, expectation in capability_matrix.capability_cases()
        ],
    )
    def test_capability_metadata_exactly_matches_the_matrix(
        self,
        language: str,
        capability: FactCapability,
        expectation: CapabilityExpectation,
    ) -> None:
        row = self.capability_matrix.languages[language]
        code_map = self.application.generate_map(
            language,
            self.repository / row.fixtures.reference.root.value,
            self.scan_policy(),
        )
        declared = {coverage.capability: coverage for coverage in code_map.producer.capabilities}

        assert declared[capability].status is expectation.status
        assert declared[capability].explanation == expectation.explanation
        assert FixtureCapabilityEvidence().capability_evidence(code_map, capability) == expectation.evidence

    @pytest.mark.parametrize(
        ("language", "family", "expectation"),
        capability_matrix.relationship_cases(),
        ids=[f"{language}-{family.value}" for language, family, expectation in capability_matrix.relationship_cases()],
    )
    def test_relationship_metadata_exactly_matches_the_matrix(
        self,
        language: str,
        family: RelationshipFamily,
        expectation: RelationshipExpectation,
    ) -> None:
        row = self.capability_matrix.languages[language]
        code_map = self.application.generate_map(
            language,
            self.repository / row.fixtures.reference.root.value,
            self.scan_policy(),
        )
        coverage = {item.family: item for item in code_map.producer.relationship_capabilities}[family]

        assert coverage.semantics is expectation.semantics
        assert coverage.semantics_explanation == expectation.semantics_explanation
        assert coverage.inventory is expectation.inventory
        assert coverage.inventory_explanation == expectation.inventory_explanation
        assert FixtureCapabilityEvidence().relationship_evidence(code_map, family) == expectation.evidence

    @pytest.mark.parametrize(
        ("language", "expectation"),
        capability_matrix.parameter_kind_cases(),
        ids=tuple(capability_matrix.languages),
    )
    def test_parameter_kinds_exactly_match_the_matrix_partition(
        self,
        language: str,
        expectation: ParameterKindExpectation,
    ) -> None:
        source = Path(expectation.source)
        code_map = self.application.generate_map(
            language,
            self.repository / source.parents[1],
            self.scan_policy(),
        )

        assert FixtureCapabilityEvidence().parameter_kinds(code_map) == tuple(sorted(expectation.present))

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_member_ownership_is_exact_for_every_language(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.repository / row.fixtures.reference.root.value,
            self.scan_policy(),
        )

        for source in code_map.extraction.files.values():
            for declaration in source.declarations:
                assert all(
                    member.owner_declaration_id == declaration.declaration_id
                    for member in (*declaration.methods, *declaration.abstract_methods, *declaration.properties)
                )

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.type_references
        ),
    )
    def test_type_reference_limitations_match_recursive_public_evidence(
        self,
        language: str,
        limitation: TypeReferenceLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(language, self.type_reference_root(language), self.scan_policy())
        evidence = FixtureCapabilityEvidence()

        assert evidence.type_reference_names(code_map) == limitation.present_reference_names
        assert evidence.nested_type_reference_names(code_map) == limitation.present_nested_reference_names
        assert evidence.type_kind_count(code_map, "absent") == limitation.absent_slot_count
        assert evidence.type_kind_count(code_map, "unsupported") == limitation.unsupported_slot_count

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(
            (language, row)
            for language, row in capability_matrix.languages.items()
            if row.capabilities[FactCapability.TYPE_REFERENCES].status is CapabilityStatus.SUPPORTED
        ),
    )
    def test_supported_type_reference_absence_is_explicit(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        code_map = self.application.generate_map(language, self.type_reference_root(language), self.scan_policy())
        evidence = FixtureCapabilityEvidence()
        slot_count = evidence.type_slot_count(code_map)

        assert slot_count > 0
        assert evidence.type_kind_count(code_map, "absent") == slot_count

    @pytest.mark.parametrize(
        ("language", "row"),
        tuple(capability_matrix.languages.items()),
        ids=tuple(capability_matrix.languages),
    )
    def test_empty_source_has_a_complete_empty_type_observation(
        self,
        language: str,
        row: LanguageCapabilityRow,
    ) -> None:
        root = self.type_reference_root(language)
        cases = row.fixtures.type_references.cases.value
        code_map = self.application.generate_map(
            language,
            root,
            self.configured_scan_policy((cases.as_posix(),), False),
        )

        assert len(code_map.extraction.files) == 1
        assert FixtureCapabilityEvidence().type_slot_count(code_map) == 0

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.symbols
        ),
    )
    def test_symbol_limitations_match_public_evidence(
        self,
        language: str,
        limitation: SymbolLimitationExpectation,
    ) -> None:
        evidence = FixtureCapabilityEvidence().declaration_names(
            self.application.generate_map(language, self.capability_gap_root(language), self.scan_policy())
        )

        assert set(limitation.present_declaration_names) <= set(evidence)
        assert set(limitation.absent_declaration_names).isdisjoint(evidence)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.callables
        ),
    )
    def test_callable_limitations_match_public_evidence(
        self,
        language: str,
        limitation: CallableLimitationExpectation,
    ) -> None:
        evidence = FixtureCapabilityEvidence().callable_names(
            self.application.generate_map(language, self.capability_gap_root(language), self.scan_policy())
        )

        assert set(limitation.present_callable_names) <= set(evidence)
        assert set(limitation.absent_callable_names).isdisjoint(evidence)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.calls
        ),
    )
    def test_call_limitations_match_public_evidence(
        self,
        language: str,
        limitation: CallLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(language, self.capability_gap_root(language), self.scan_policy())
        evidence = FixtureCapabilityEvidence()

        assert set(limitation.present_resolutions) <= set(evidence.call_resolutions(code_map))
        assert set(limitation.absent_target_names).isdisjoint(evidence.call_target_names(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.parameters
        ),
    )
    def test_parameter_limitations_match_public_evidence(
        self,
        language: str,
        limitation: ParameterLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(language, self.capability_gap_root(language), self.scan_policy())
        evidence = FixtureCapabilityEvidence()

        assert set(limitation.present_parameter_kinds) <= set(evidence.parameter_kinds(code_map))
        assert set(limitation.unrepresented_authored_parameters).isdisjoint(evidence.parameter_names(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.attributes
        ),
    )
    def test_attribute_limitations_match_public_evidence(
        self,
        language: str,
        limitation: AttributeLimitationExpectation,
    ) -> None:
        evidence = FixtureCapabilityEvidence().attribute_names(
            self.application.generate_map(language, self.capability_gap_root(language), self.scan_policy())
        )

        assert set(limitation.present_attribute_names) <= set(evidence)
        assert set(limitation.absent_attribute_names).isdisjoint(evidence)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.annotations
        ),
    )
    def test_annotation_limitations_match_public_evidence(
        self,
        language: str,
        limitation: AnnotationLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()

        assert set(limitation.present_annotations) <= set(evidence.annotations(code_map))
        assert set(limitation.absent_annotations).isdisjoint(evidence.annotations(code_map))
        assert set(limitation.absent_attribute_names).isdisjoint(evidence.attribute_names(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.modifiers
        ),
    )
    def test_modifier_limitations_match_public_evidence(
        self,
        language: str,
        limitation: ModifierLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()
        represented = {
            *evidence.visibility_intents(code_map),
            *evidence.callable_kinds(code_map),
            *(member_kind.value for member_kind in evidence.member_kinds(code_map)),
        }

        assert set(limitation.present_visibility_intents) <= set(evidence.visibility_intents(code_map))
        assert set(limitation.present_callable_kinds) <= set(evidence.callable_kinds(code_map))
        assert set(limitation.present_member_kinds) <= set(evidence.member_kinds(code_map))
        assert set(limitation.unrepresented_authored_modifiers).isdisjoint(represented)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.assigned_values
        ),
    )
    def test_assigned_value_limitations_match_public_evidence(
        self,
        language: str,
        limitation: AssignedValueLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()
        observed = evidence.assigned_value_kinds(code_map)

        assert set(limitation.present_attribute_names) <= set(evidence.attribute_names(code_map))
        assert set(limitation.absent_attribute_names).isdisjoint(evidence.attribute_names(code_map))
        assert all(observed[name] == kinds for name, kinds in limitation.expected_value_kinds.items())

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.namespaces
        ),
    )
    def test_namespace_limitations_match_public_evidence(
        self,
        language: str,
        limitation: NamespaceLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )

        assert set(limitation.absent_namespaces).isdisjoint(FixtureCapabilityEvidence().namespaces(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.composition
        ),
    )
    def test_composition_limitations_match_public_evidence(
        self,
        language: str,
        limitation: CompositionLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()

        assert set(limitation.present_relations) <= set(evidence.declaration_relations(code_map))
        assert set(limitation.absent_endpoints).isdisjoint(evidence.declaration_relation_endpoints(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.dependencies
        ),
    )
    def test_dependency_limitations_match_public_evidence(
        self,
        language: str,
        limitation: DependencyLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        observed = FixtureCapabilityEvidence().dependencies(code_map)

        assert set(limitation.present_dependencies) <= set(observed)
        assert set(limitation.absent_dependencies).isdisjoint(observed)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in row.capability_limitations.spans
        ),
    )
    def test_span_limitations_match_public_evidence(
        self,
        language: str,
        limitation: SpanLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        observed = FixtureCapabilityEvidence().exact_span_owners(code_map)

        assert set(limitation.present_exact_span_owners) <= set(observed)
        assert set(limitation.absent_exact_span_owners).isdisjoint(observed)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in (
                *row.relationship_limitations.declaration_semantics,
                *row.relationship_limitations.declaration_inventory,
            )
        ),
    )
    def test_declaration_relationship_limitations_match_public_evidence(
        self,
        language: str,
        limitation: DeclarationRelationshipLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()

        assert set(limitation.present_relations) <= set(evidence.declaration_relations(code_map))
        assert set(limitation.present_endpoints) <= set(evidence.declaration_relation_endpoints(code_map))
        assert set(limitation.absent_endpoints).isdisjoint(evidence.declaration_relation_endpoints(code_map))

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in (
                *row.relationship_limitations.member_semantics,
                *row.relationship_limitations.member_inventory,
            )
        ),
    )
    def test_member_relationship_limitations_match_public_evidence(
        self,
        language: str,
        limitation: MemberRelationshipLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        evidence = FixtureCapabilityEvidence()
        value_kinds = {kind for kinds in evidence.assigned_value_kinds(code_map).values() for kind in kinds}

        assert set(limitation.present_attribute_names) <= set(evidence.attribute_names(code_map))
        assert set(limitation.absent_attribute_names).isdisjoint(evidence.attribute_names(code_map))
        assert set(limitation.present_value_kinds) <= value_kinds
        assert set(limitation.absent_value_kinds).isdisjoint(value_kinds)

    @pytest.mark.parametrize(
        ("language", "limitation"),
        tuple(
            (language, limitation)
            for language, row in capability_matrix.languages.items()
            for limitation in (
                *row.relationship_limitations.dependency_semantics,
                *row.relationship_limitations.dependency_inventory,
            )
        ),
    )
    def test_dependency_relationship_limitations_match_public_evidence(
        self,
        language: str,
        limitation: DependencyRelationshipLimitationExpectation,
    ) -> None:
        code_map = self.application.generate_map(
            language,
            self.capability_gap_root(language),
            self.scan_policy(),
        )
        observed = FixtureCapabilityEvidence().dependencies(code_map)

        assert set(limitation.present_dependencies) <= set(observed)
        assert set(limitation.absent_dependencies).isdisjoint(observed)
