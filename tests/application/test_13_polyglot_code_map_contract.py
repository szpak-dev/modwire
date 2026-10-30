import shutil

import pytest
from pydantic import ValidationError

from modwire.application import (
    CodeMap,
    CodeValidationError,
    FactCapability,
    FileId,
    RelationshipFamily,
    SourceAssignedValueKind,
)

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
        language, bundle = next(iter(self.contract.matrix.languages.items()))
        pair = self.contract.matrix.index.languages[language]
        contract_path = self.workspace / pair.contract.value
        original_contract = contract_path.read_text(encoding="utf-8")
        major = bundle.contract.runtime.version.major
        contract_path.write_text(
            original_contract.replace(f"major: {major}", f'major: "{major}"', 1),
            encoding="utf-8",
        )

        with pytest.raises(ValidationError, match="int_type"):
            PolyglotFixtureContract(self.workspace)

        contract_path.write_text(
            original_contract.replace("state: present", "state: unsupported", 1),
            encoding="utf-8",
        )
        with pytest.raises(ValidationError, match="unsupported claim state requires a type-slot observation"):
            PolyglotFixtureContract(self.workspace)

        contract_path.write_text(original_contract, encoding="utf-8")
        PolyglotFixtureContract(self.workspace)

    def test_runtime_and_evidence_attacks_are_rejected_before_each_contract_recovers(self) -> None:
        self.copy_contract_documents()
        for language, bundle in self.contract.matrix.languages.items():
            pair = self.contract.matrix.index.languages[language]
            path = self.workspace / pair.contract.value
            original = path.read_text(encoding="utf-8")
            document = bundle.contract.model_dump_json()
            runtime = bundle.contract.runtime
            other = next(
                candidate.contract.runtime.runtime
                for candidate in self.contract.matrix.languages.values()
                if candidate.contract.runtime.runtime != runtime.runtime
            )
            path.write_text(
                document.replace(f'"runtime":"{runtime.runtime.value}"', f'"runtime":"{other.value}"', 1),
                encoding="utf-8",
            )
            with pytest.raises(ValueError):
                PolyglotFixtureContract(self.workspace).validate_runtime_bindings(self.application)

            path.write_text(document.replace('"evidence":"supported"', '"evidence":"boundary"'), encoding="utf-8")
            with pytest.raises(ValidationError, match="lacks supported evidence"):
                PolyglotFixtureContract(self.workspace)

            if runtime.packages:
                package = runtime.packages[0].model_dump_json()
                path.write_text(
                    document.replace(f'"packages":[{package}]', f'"packages":[{package},{package}]', 1),
                    encoding="utf-8",
                )
                with pytest.raises(ValidationError, match="package identities contain duplicates"):
                    PolyglotFixtureContract(self.workspace)
            else:
                package = next(
                    package
                    for candidate in self.contract.matrix.languages.values()
                    for package in candidate.contract.runtime.packages
                ).model_dump_json()
                path.write_text(document.replace('"packages":[]', f'"packages":[{package}]', 1), encoding="utf-8")
                with pytest.raises(ValidationError, match="gem packages require the Ruby runtime"):
                    PolyglotFixtureContract(self.workspace)

            path.write_text(original, encoding="utf-8")
            PolyglotFixtureContract(self.workspace)

    def test_assigned_value_expectations_reject_the_same_invalid_state_as_public_facts(self) -> None:
        self.copy_contract_documents()
        attacks = 0
        for scenario, sources in self.contract.matrix.catalog.source_documents.items():
            for source_id, source_path in sources.items():
                path = self.workspace / source_path.value
                original = path.read_text(encoding="utf-8")
                source = self.contract.matrix.catalog.expected[scenario].extraction.files[source_id]
                sites = tuple(
                    (declaration_index, property_index, value_index)
                    for declaration_index, declaration in enumerate(source.declarations)
                    for property_index, property_ in enumerate(declaration.properties)
                    for value_index, value in enumerate(property_.assigned_values)
                    if value.kind is SourceAssignedValueKind.UNASSIGNED
                )
                if not sites:
                    continue
                declaration_index, property_index, value_index = sites[0]
                declaration = source.declarations[declaration_index]
                property_ = declaration.properties[property_index]
                attacked_property = property_.model_copy(
                    update={
                        "assigned_values": tuple(
                            value.model_copy(update={"expression": "fabricated", "reference": "fabricated"})
                            if index == value_index
                            else value
                            for index, value in enumerate(property_.assigned_values)
                        )
                    }
                )
                attacked_declaration = declaration.model_copy(
                    update={
                        "properties": tuple(
                            attacked_property if index == property_index else value
                            for index, value in enumerate(declaration.properties)
                        )
                    }
                )
                attacked = source.model_copy(
                    update={
                        "declarations": tuple(
                            attacked_declaration if index == declaration_index else value
                            for index, value in enumerate(source.declarations)
                        )
                    }
                )
                path.write_text(attacked.model_dump_json(), encoding="utf-8")
                with pytest.raises(CodeValidationError):
                    PolyglotFixtureContract(self.workspace)
                path.write_text(original, encoding="utf-8")
                PolyglotFixtureContract(self.workspace)
                attacks += 1
        assert attacks > 0

    def test_each_nonempty_owned_source_has_evidence_that_rejects_erased_facts(self) -> None:
        extracted: dict[tuple[str, str], CodeMap] = {}
        for language, scenario in self.contract.scenario_cases():
            key = (language.value, scenario.fixture.value)
            if key not in extracted:
                extracted[key] = self.application.generate_map(
                    language.value, str(self.contract.fixture_root(language, scenario.fixture)), self.scan_policy()
                )
            code_map = extracted[key]
            source_id = FileId(scenario.source.value.as_posix())
            source = code_map.extraction.files[source_id]
            erased = source.model_copy(
                update={
                    "declarations": (),
                    "functions": (),
                    "values": (),
                    "callable_values": (),
                    "anonymous_callables": (),
                    "calls": (),
                    "declaration_relations": (),
                    "namespaces": (),
                    "imports": [],
                    "exports": [],
                }
            )
            if source == erased:
                continue
            files = dict(code_map.extraction.files)
            files[source_id] = erased
            attacked = code_map.model_copy(
                update={"extraction": code_map.extraction.model_copy(update={"files": files})}
            )
            related = (
                candidate
                for candidate_language, candidate in self.contract.scenario_cases()
                if candidate_language == language
                and candidate.fixture is scenario.fixture
                and candidate.source == scenario.source
            )
            assert any(
                not result.satisfied
                for candidate in related
                for result in self.contract.evaluate_scenario(attacked, candidate)
            ), f"{language.value}:{scenario.fixture.value}:{source_id}"

    def test_type_slot_presence_never_accepts_absent_or_unsupported_types(self) -> None:
        for language, scenario in self.contract.scenario_cases():
            for wrapped in scenario.claims:
                claim = wrapped.root
                if claim.observation.root.kind != "type_slot" or claim.state is claim.state.PRESENT:
                    continue
                code_map = self.application.generate_map(
                    language.value, str(self.contract.fixture_root(language, scenario.fixture)), self.scan_policy()
                )
                present = claim.model_copy(update={"state": claim.state.PRESENT})
                attacked = scenario.model_copy(update={"claims": (wrapped.model_copy(update={"root": present}),)})
                assert not self.contract.evaluate_scenario(code_map, attacked)[0].satisfied

    def test_matrix_exactly_covers_the_public_language_and_capability_vocabularies(self) -> None:
        self.contract.validate_runtime_bindings(self.application)
        languages = tuple(language.value for language in self.contract.matrix.languages)

        assert languages == self.application.supported_languages()
        assert len(self.contract.capability_cases()) == len(languages) * len(FactCapability)
        assert len(self.contract.relationship_cases()) == len(languages) * len(RelationshipFamily)
        assert {
            (language.value, capability) for language, capability, _expectation in self.contract.capability_cases()
        } == {(language, capability) for language in languages for capability in FactCapability}
        assert {
            (language.value, relationship)
            for language, relationship, _expectation in self.contract.relationship_cases()
        } == {(language, relationship) for language in languages for relationship in RelationshipFamily}

    def test_every_owned_fixture_inventory_is_exactly_declared_by_the_matrix(self) -> None:
        self.contract.validate_inventories()

    def test_every_capability_and_relationship_claim_matches_public_extraction(self) -> None:
        extracted: dict[tuple[str, str], CodeMap] = {}

        for language, binding in self.contract.scenario_bindings():
            key = (language.value, binding.fixture.root.value.as_posix())
            extracted[key] = self.application.generate_map(
                language.value,
                str(self.contract.binding_root(binding)),
                self.contract.binding_policy(binding),
            )
            assert all(
                result.satisfied for result in self.contract.evaluate_binding(language, extracted[key], binding)
            ), f"{language.value}:{binding.scenario.value}"

        for language, scenario in self.contract.scenario_cases():
            key = (
                language.value,
                self.contract.fixture_root(language, scenario.fixture).relative_to(self.repository).as_posix(),
            )
            if key not in extracted:
                extracted[key] = self.application.generate_map(
                    language.value,
                    str(self.contract.fixture_root(language, scenario.fixture)),
                    self.scan_policy(),
                )
            results = self.contract.evaluate_scenario(extracted[key], scenario)
            for claim, result in zip(scenario.claims, results, strict=True):
                assert result.satisfied, f"{language.value}:{scenario.name.value}:{claim.model_dump_json()}"

    def test_every_published_coverage_cell_exactly_matches_the_matrix(self) -> None:
        extracted = {
            language: self.application.generate_map(
                language.value,
                str(self.repository / projection.fixture.root.value),
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
                str(self.repository / projection.fixture.root.value),
                self.configured_scan_policy(("ignored/**",), False),
            )

            assert self.contract.project_reference(actual, projection) == self.contract.matrix.reference_code_map, (
                language.value
            )
