import shutil

import pytest
from pydantic import ValidationError

from modwire.application import FactCapability, RelationshipFamily

from ..support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ..support.code_map_fixture.fixture_contract_error import FixtureContractError
from .base_test import ApplicationTestCase


class TestPolyglotCodeMapContract(ApplicationTestCase):
    contract = PolyglotFixtureContract(ApplicationTestCase.repository)

    def copy_contract_documents(self) -> None:
        shutil.copyfile(
            self.repository / "language-capabilities.yaml",
            self.workspace / "language-capabilities.yaml",
        )
        shutil.copytree(
            self.repository / "language-capabilities",
            self.workspace / "language-capabilities",
        )
        reference = self.workspace / "tests/fixtures/code_map/reference_shop/expected_code_map.json"
        reference.parent.mkdir(parents=True)
        shutil.copyfile(
            self.repository / "tests/fixtures/code_map/reference_shop/expected_code_map.json",
            reference,
        )

    def test_document_inventory_attacks_are_rejected_before_the_complete_graph_recovers(self) -> None:
        self.copy_contract_documents()
        pair = next(iter(self.contract.matrix.index.languages.values()))
        source = self.repository / pair.contract.value
        target = self.workspace / pair.contract.value

        target.unlink()
        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            PolyglotFixtureContract(self.workspace)
        shutil.copyfile(source, target)

        attack = target.parent / "attack.yaml"
        attack.write_text("language: attack\n", encoding="utf-8")
        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            PolyglotFixtureContract(self.workspace)
        attack.unlink()

        target.unlink()
        target.mkdir()
        with pytest.raises(FixtureContractError, match="language document inventory mismatch"):
            PolyglotFixtureContract(self.workspace)
        target.rmdir()
        shutil.copyfile(source, target)

        PolyglotFixtureContract(self.workspace)

    def test_strict_document_attacks_are_rejected_before_the_original_contract_recovers(self) -> None:
        self.copy_contract_documents()
        index = self.workspace / "language-capabilities.yaml"
        original_index = index.read_text(encoding="utf-8")
        index.write_text(original_index.replace("schema_version: 1", "schema_version: 2", 1), encoding="utf-8")

        with pytest.raises(ValidationError, match="literal_error"):
            PolyglotFixtureContract(self.workspace)

        index.write_text(original_index, encoding="utf-8")
        pair = next(iter(self.contract.matrix.index.languages.values()))
        contract_path = self.workspace / pair.contract.value
        original_contract = contract_path.read_text(encoding="utf-8")
        contract_path.write_text(f"{original_contract}unexpected_contract_field: true\n", encoding="utf-8")

        with pytest.raises(ValidationError, match="extra_forbidden"):
            PolyglotFixtureContract(self.workspace)

        contract_path.write_text(original_contract, encoding="utf-8")
        PolyglotFixtureContract(self.workspace)

    def test_matrix_exactly_covers_the_public_language_and_capability_vocabularies(self) -> None:
        languages = tuple(language.value for language in self.contract.matrix.languages)

        assert languages == self.application.supported_languages()
        assert len(self.contract.capability_cases()) == len(languages) * len(FactCapability)
        assert len(self.contract.relationship_cases()) == len(languages) * len(RelationshipFamily)
        assert {
            (language.value, capability) for language, capability, expectation in self.contract.capability_cases()
        } == {(language, capability) for language in languages for capability in FactCapability}
        assert {
            (language.value, relationship) for language, relationship, expectation in self.contract.relationship_cases()
        } == {(language, relationship) for language in languages for relationship in RelationshipFamily}

    def test_every_owned_fixture_inventory_is_exactly_declared_by_the_matrix(self) -> None:
        self.contract.validate_inventories()

    def test_every_capability_and_relationship_claim_matches_public_extraction(self) -> None:
        extracted = {}

        for language, scenario in self.contract.scenario_cases():
            key = (language, scenario.fixture)
            if key not in extracted:
                extracted[key] = self.application.generate_map(
                    language.value,
                    self.contract.fixture_root(language, scenario.fixture),
                    self.scan_policy(),
                )
            results = self.contract.evaluate_scenario(extracted[key], scenario)
            for claim, result in zip(scenario.claims, results, strict=True):
                assert result.satisfied, f"{language.value}:{scenario.name.value}:{claim.model_dump_json()}"

    def test_every_published_coverage_cell_exactly_matches_the_matrix(self) -> None:
        extracted = {
            language: self.application.generate_map(
                language.value,
                self.repository / projection.fixture.root.value,
                self.configured_scan_policy(("ignored/**",), False),
            )
            for language, projection in self.contract.projection_cases()
        }

        for language, capability, expectation in self.contract.capability_cases():
            declared = {coverage.capability: coverage for coverage in extracted[language].producer.capabilities}[
                capability
            ]
            assert declared.status is expectation.status, f"{language.value}:{capability.value}:status"
            assert declared.explanation == expectation.explanation.value, (
                f"{language.value}:{capability.value}:explanation"
            )

        for language, relationship, expectation in self.contract.relationship_cases():
            declared = {
                coverage.family: coverage for coverage in extracted[language].producer.relationship_capabilities
            }[relationship]
            assert declared.semantics is expectation.semantics, f"{language.value}:{relationship.value}:semantics"
            assert declared.semantics_explanation == expectation.semantics_explanation.value, (
                f"{language.value}:{relationship.value}:semantics_explanation"
            )
            assert declared.inventory is expectation.inventory, f"{language.value}:{relationship.value}:inventory"
            assert declared.inventory_explanation == expectation.inventory_explanation.value, (
                f"{language.value}:{relationship.value}:inventory_explanation"
            )

    def test_every_language_exactly_projects_to_the_common_reference_code_map(self) -> None:
        for language, projection in self.contract.projection_cases():
            actual = self.application.generate_map(
                language.value,
                self.repository / projection.fixture.root.value,
                self.configured_scan_policy(("ignored/**",), False),
            )

            assert self.contract.project_reference(actual, projection) == self.contract.matrix.reference_code_map, (
                language.value
            )
