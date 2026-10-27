from pathlib import Path

import pytest
from pydantic import ValidationError

from modwire.application import (
    CodeMap,
    FactCapability,
    RelationshipFamily,
)

from ..support.code_map_fixture.capability_evidence import FixtureCapabilityEvidence
from ..support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ..support.code_map_fixture.fixture_contract_error import FixtureContractError
from ..support.code_map_fixture.language_capability_matrix.expectations.capability import CapabilityExpectation
from ..support.code_map_fixture.language_capability_matrix.expectations.relationship import RelationshipExpectation
from ..support.code_map_fixture.language_capability_matrix.expectations.scenario import (
    LimitationScenarioExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.annotation import (
    AnnotationLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.attribute import (
    AttributeLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.call import (
    CallLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.callable import (
    CallableLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.composition import (
    CompositionLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.dependency import (
    DependencyLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.modifier import (
    ModifierLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.namespace import (
    NamespaceLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.parameter import (
    ParameterLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.span import (
    SpanLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.symbol import (
    SymbolLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.capability.value import (
    AssignedValueLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.relationship.declaration import (
    DeclarationRelationshipLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.relationship.dependency import (
    DependencyRelationshipLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.limits.relationship.member import (
    MemberRelationshipLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.matrix import LanguageCapabilityMatrix
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from ..support.code_map_fixture.language_capability_matrix.row import LanguageCapabilityRow
from ..support.code_map_fixture.projector import FixtureCodeMapProjector
from .base_test import ApplicationTestCase


class TestPolyglotCodeMapContract(ApplicationTestCase):
    capability_matrix = LanguageCapabilityMatrixReader().read(
        ApplicationTestCase.repository / "language-capabilities.yaml"
    )

    def capability_gap_root(self, language: str) -> Path:
        return self.repository / self.capability_matrix.languages[language].fixtures.capability_gap_root

    def test_missing_language_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract()
        expected = tuple(sorted(self.capability_matrix.languages))
        row = next(iter(self.capability_matrix.languages.values()))
        root = (self.repository / row.fixtures.reference_root).parent

        with pytest.raises(FixtureContractError, match="language inventory mismatch"):
            contract.validate_language_inventory(root, expected[1:])

        contract.validate_language_inventory(root, expected)

    def test_extra_language_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract()
        expected = tuple(sorted(self.capability_matrix.languages))
        row = next(iter(self.capability_matrix.languages.values()))
        root = (self.repository / row.fixtures.reference_root).parent

        with pytest.raises(FixtureContractError, match="language inventory mismatch"):
            contract.validate_language_inventory(root, (*expected, "attack"))

        contract.validate_language_inventory(root, expected)

    def test_missing_source_attack_is_rejected_before_valid_inventory_recovers(self) -> None:
        contract = PolyglotFixtureContract()
        row = next(iter(self.capability_matrix.languages.values()))
        root = self.repository / row.fixtures.reference_root
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

    def test_extra_nested_matrix_field_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["convention"]["attack"] = True

        with pytest.raises(ValidationError, match="extra_forbidden"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_parsed_nested_matrix_model_reassignment_attack_is_rejected(self) -> None:
        convention = next(iter(self.capability_matrix.languages.values())).convention
        suffix = convention.suffix

        with pytest.raises(ValidationError, match="frozen_instance"):
            convention.suffix = ".attack"

        assert convention.suffix == suffix

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
        attacked["languages"][language]["fixtures"]["manifest_sources"]["canonical"] = (
            "canonical/src/example.unsupported"
        )

        with pytest.raises(ValidationError, match="manifest inventory contains a non-source path"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_manifest_source_outside_its_named_scenario_attack_is_rejected(self) -> None:
        language = next(iter(self.capability_matrix.languages))
        attacked = self.capability_matrix.model_dump(mode="json")
        attacked["languages"][language]["fixtures"]["manifest_sources"]["canonical"] = attacked["languages"][language][
            "fixtures"
        ]["manifest_sources"]["calls"]

        with pytest.raises(ValidationError, match="manifest source is outside its named scenario"):
            LanguageCapabilityMatrix.model_validate(attacked)

    def test_wrong_filename_attack_is_rejected_before_matrix_conventions_accept_reference_sources(self) -> None:
        contract = PolyglotFixtureContract()

        for row in self.capability_matrix.languages.values():
            assert not row.convention.accepts_source_path(f"src/example{row.convention.suffix}.attack")
            assert all(
                row.convention.accepts_source_path(path)
                for path in contract.source_paths(self.repository / row.fixtures.reference_root)
            )

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
        contract = PolyglotFixtureContract()
        fixture_root = self.capability_gap_root(next(iter(self.capability_matrix.languages))).parent
        expected_languages = tuple(
            sorted(language for language, row in self.capability_matrix.languages.items() if row.scenarios)
        )

        contract.validate_language_inventory(fixture_root, expected_languages)
        for language, row in self.capability_matrix.languages.items():
            expected_sources = tuple(sorted({scenario.source for scenario in row.scenarios}))
            contract.validate_source_inventory(fixture_root / language, expected_sources)

    def test_implementation_manifest_fixture_inventory_covers_every_matrix_language(self) -> None:
        root = self.repository / "tests/fixtures/implementation_manifest"
        contract = PolyglotFixtureContract()

        contract.validate_language_inventory(root, tuple(sorted(self.capability_matrix.languages)))
        for language, row in self.capability_matrix.languages.items():
            contract.validate_source_inventory(
                self.repository / row.fixtures.manifest_root,
                tuple(sorted(row.fixtures.manifest_sources.values())),
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
        source = (self.capability_gap_root(language) / scenario.source).read_text(encoding="utf-8")

        assert all(authored_syntax in source for authored_syntax in scenario.authored_syntax)

    def test_reference_projects_have_the_exact_matrix_driven_source_inventory(self) -> None:
        contract = PolyglotFixtureContract()
        master = CodeMap.model_validate_json(
            (self.repository / self.capability_matrix.reference_projection).read_text(encoding="utf-8")
        )
        declarations = {
            str(source_id): source.declarations[0].name for source_id, source in master.extraction.files.items()
        }

        for row in self.capability_matrix.languages.values():
            expected = tuple(
                sorted(
                    (
                        row.convention.source_path("ignored/generated_order", "GeneratedOrder"),
                        *(
                            row.convention.source_path(source_id, declaration_name)
                            for source_id, declaration_name in declarations.items()
                        ),
                    )
                )
            )
            contract.validate_source_inventory(self.repository / row.fixtures.reference_root, expected)

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
            (self.repository / self.capability_matrix.reference_projection).read_text(encoding="utf-8")
        )
        actual = self.application.generate_map(
            language,
            self.repository / row.fixtures.reference_root,
            self.configured_scan_policy(("ignored/**",), False),
        )

        assert FixtureCodeMapProjector().project(actual) == expected

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
            self.repository / row.fixtures.reference_root,
            self.scan_policy(),
        )
        declared = {coverage.capability: coverage for coverage in code_map.producer.capabilities}

        assert declared[capability].status is expectation.status
        assert declared[capability].explanation == expectation.explanation

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
            self.repository / row.fixtures.reference_root,
            self.scan_policy(),
        )
        coverage = {item.family: item for item in code_map.producer.relationship_capabilities}[family]

        assert coverage.semantics is expectation.semantics
        assert coverage.semantics_explanation == expectation.semantics_explanation
        assert coverage.inventory is expectation.inventory
        assert coverage.inventory_explanation == expectation.inventory_explanation

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
