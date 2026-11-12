import shutil
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    FactCapability,
    RelationshipCoverage,
    RelationshipFamily,
)

from ..support.code_map_fixture.claim_result import ClaimResult
from ..support.code_map_fixture.conclusion import Conclusion
from ..support.code_map_fixture.discrepancy import Discrepancy
from ..support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ..support.code_map_fixture.fixture_contract_error import FixtureContractError
from ..support.code_map_fixture.language_capability_matrix.oracle.binding import LanguageScenarioBinding
from ..support.code_map_fixture.language_capability_matrix.oracle.documents.catalog import ScenarioCatalogDocument
from ..support.code_map_fixture.language_capability_matrix.oracle.documents.language_applicability import (
    LanguageApplicability,
)
from ..support.code_map_fixture.language_capability_matrix.oracle.scenario_kind import ScenarioKind
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from ..support.code_map_fixture.language_capability_matrix.values.enums.observation_kind import ObservationKind
from ..support.code_map_fixture.language_capability_matrix.values.names.identifier import Identifier
from ..support.code_map_fixture.language_capability_matrix.values.names.language_id import LanguageId
from ..support.code_map_fixture.language_capability_matrix.values.names.scenario_id import ScenarioId
from ..support.code_map_fixture.matrix_report import ExtractionMatrixReport
from ..support.code_map_fixture.runtime_contract_error import RuntimeContractError
from ..support.extraction_matrix import ExtractionMatrixCommand
from .base_test import ApplicationTestCase


class TestPolyglotCodeMapContract(ApplicationTestCase):
    contract = PolyglotFixtureContract(ApplicationTestCase.repository)

    def structural_binding(self, language: str) -> LanguageScenarioBinding:
        return next(
            binding
            for candidate, binding in self.contract.scenario_bindings()
            if candidate.value == language and binding.scenario == ScenarioId("structural")
        )

    def copy_structural_sources(self) -> Path:
        root = self.workspace / "structural"
        shutil.copytree(self.repository / "tests/fixtures/structural_fidelity", root)
        return root

    def test_matrix_report_retains_five_language_gaps_and_native_provenance(self) -> None:
        output = self.workspace / "matrix.json"
        assert ExtractionMatrixCommand(self.application).run((str(self.repository), str(output))) == 1
        report = ExtractionMatrixReport.model_validate_json(output.read_text())

        assert not report.conforms and not report.regression_passes
        assert set(report.results) == set(self.contract.matrix.languages)
        assert sum(len(maps[ScenarioId("structural")].extraction.files) for maps in report.observations.values()) == 7
        assert all(
            result.expected and result.actual and result.owner_issue > 0
            for scenarios in report.results.values()
            for results in scenarios.values()
            for result in results
        )
        assert any(
            Discrepancy.WRONG_OWNER in result.discrepancies
            for result in report.results[LanguageId("ruby")][ScenarioId("structural")]
        )
        assert all(
            any(Discrepancy.MODEL_GAP in result.discrepancies for result in scenarios[ScenarioId("structural")])
            for scenarios in report.results.values()
        )
        assert "N/A" in report.table() and "Conformance: FAIL" in report.table()

    def copy_matrix_repository(self) -> None:
        self.copy_contract_documents()
        for collection in self.contract.matrix.index.fixture_collections:
            shutil.copytree(self.repository / collection.root.value, self.workspace / collection.root.value)

    def test_shared_model_limitation_rejects_case_overrides_and_has_one_owner(self) -> None:
        self.copy_matrix_repository()
        source = self.workspace / "language-capabilities/scenarios/structural/python/src/example.py.json"
        original = source.read_text()
        source.write_text(
            "\n".join(
                '    "local_inventory": {"owner_issue": 999}' if '"local_inventory":' in line else line
                for line in original.splitlines()
            )
        )
        output = self.workspace / "matrix.json"
        command = ExtractionMatrixCommand(self.application)
        assert command.run((str(self.workspace), str(output))) == 2
        failure = ClaimResult.model_validate_json(output.read_text())
        assert failure.discrepancies == (Discrepancy.INVALID_EVIDENCE,)
        source.write_text(original)

        catalogue = self.workspace / "language-capabilities/scenarios/catalog.yaml"
        catalogue.write_text(catalogue.read_text().replace("owner_issue: 104", "owner_issue: 999"))
        assert command.run((str(self.workspace), str(output))) == 1
        report = ExtractionMatrixReport.model_validate_json(output.read_text())
        findings = tuple(
            result
            for cases in report.results.values()
            for results in cases.values()
            for result in results
            if result.subject.endswith(":local_inventory")
        )
        assert len(findings) == 6
        assert all(result.owner_issue == 999 for result in findings)

    def test_removed_evidence_cannot_be_replaced_by_unrelated_passing_scenarios(self) -> None:
        self.copy_matrix_repository()
        catalogue = self.workspace / "language-capabilities/scenarios/catalog.yaml"
        document = LanguageCapabilityMatrixReader().read_document(catalogue, ScenarioCatalogDocument)
        removed = tuple(name for name, gap in document.model_gaps.items() if gap.conclusion is Conclusion.QUALIFIERS)
        for name in removed:
            del document.model_gaps[name]
        python = LanguageId("python")
        applicability = document.obligations[Conclusion.DECLARATIONS].languages[python]
        document.obligations[Conclusion.DECLARATIONS].languages[python] = LanguageApplicability(
            applicable=True,
            reason=applicability.reason,
            evidence=(*applicability.evidence, ScenarioId("extensions")),
        )
        catalogue.write_text(document.model_dump_json())
        scenario = ScenarioId("structural")
        expected = self.contract.matrix.catalog.expected[scenario].root
        assert expected.kind is ScenarioKind.SOURCE_FACTS
        adapter = TypeAdapter(dict[Identifier, str])
        for source, expectation in expected.sources.items():
            path = self.workspace / self.contract.matrix.catalog.source_documents[scenario][source].value
            gaps = {name: requirement for name, requirement in expectation.gaps.items() if name not in removed}
            path.write_text(
                expectation.model_dump_json().replace(
                    '"gaps":' + adapter.dump_json(expectation.gaps).decode(),
                    '"gaps":' + adapter.dump_json(gaps).decode(),
                    1,
                )
            )

        output = self.workspace / "matrix.json"
        assert ExtractionMatrixCommand(self.application).run((str(self.workspace), str(output))) == 1
        report = ExtractionMatrixReport.model_validate_json(output.read_text())
        assert not report.conforms and not report.regression_passes
        assert next(line for line in report.table().splitlines() if line.startswith("| C09 |")) == (
            "| C09 | unassessed | unassessed | unassessed | unassessed | unassessed |"
        )
        missing = report.results[python][ScenarioId("obligation-C02")]
        assert missing[0].discrepancies == (Discrepancy.UNASSESSED,)
        assert missing[0].actual == '["extensions"]'

    def test_non_applicable_obligation_cannot_hide_conflicting_findings(self) -> None:
        self.copy_matrix_repository()
        catalogue = self.workspace / "language-capabilities/scenarios/catalog.yaml"
        document = LanguageCapabilityMatrixReader().read_document(catalogue, ScenarioCatalogDocument)
        python = LanguageId("python")
        document.obligations[Conclusion.COMPLETENESS].languages[python] = LanguageApplicability(
            applicable=False,
            reason="Example obligation is outside the selected scope.",
            evidence=(),
        )
        catalogue.write_text(document.model_dump_json())
        output = self.workspace / "matrix.json"
        assert ExtractionMatrixCommand(self.application).run((str(self.workspace), str(output))) == 1
        report = ExtractionMatrixReport.model_validate_json(output.read_text())
        assert not report.conforms and not report.regression_passes
        conflict = report.results[python][ScenarioId("obligation-C11")]
        assert conflict[0].discrepancies == (Discrepancy.INVALID_EVIDENCE,)
        row = next(line for line in report.table().splitlines() if line.startswith("| C11 |"))
        assert "invalid_evidence" in row.split("|")[2]
        assert "N/A" not in row.split("|")[2]

    def test_failed_extraction_keeps_other_native_evidence_available(self) -> None:
        self.copy_matrix_repository()
        source = self.workspace / "tests/fixtures/structural_fidelity/python/src/example.py"
        source.write_text("def broken(:\n")
        report = PolyglotFixtureContract(self.workspace).assess(self.application, "test", "test")

        assert not report.conforms and not report.regression_passes
        failure = report.results[LanguageId("python")][ScenarioId("structural")]
        assert len(failure) == 1 and failure[0].discrepancies == (Discrepancy.EXTRACTION_FAILURE,)
        assert "source_parse" in failure[0].subject
        assert ScenarioId("structural") not in report.observations[LanguageId("python")]
        assert all(
            ScenarioId("structural") in observations
            for language, observations in report.observations.items()
            if language != LanguageId("python")
        )

    def test_deleted_member_and_changed_owner_change_native_assessments(self) -> None:
        root = self.copy_structural_sources()
        java = LanguageId("java")
        binding = self.structural_binding(java.value)
        before = self.application.generate_map(java.value, str(root), self.contract.binding_policy(binding))
        before_results = self.contract.evaluate_binding(self.application, java, before, binding)
        property_result = next(
            result for result in before_results if result.subject == "java/src/Example.java:C04:properties"
        )
        assert property_result.satisfied

        source = root / "java/src/Example.java"
        source.write_text(source.read_text().replace("    int exampleValue;\n", "", 1))
        after = self.application.generate_map(java.value, str(root), self.contract.binding_policy(binding))
        assert any(
            result.subject == property_result.subject and Discrepancy.MISSING in result.discrepancies
            for result in self.contract.evaluate_binding(self.application, java, after, binding)
        )
        ruby = LanguageId("ruby")
        binding = self.structural_binding(ruby.value)
        before = self.application.generate_map(ruby.value, str(root), self.contract.binding_policy(binding))
        assert any(
            Discrepancy.WRONG_OWNER in result.discrepancies
            for result in self.contract.evaluate_binding(self.application, ruby, before, binding)
        )
        source = root / "ruby_receivers/src/example.rb"
        source.write_text(source.read_text().replace("class ExampleContainer", "class ExampleTarget", 1))
        after = self.application.generate_map(ruby.value, str(root), self.contract.binding_policy(binding))
        assert not any(
            Discrepancy.WRONG_OWNER in result.discrepancies
            for result in self.contract.evaluate_binding(self.application, ruby, after, binding)
        )

    def test_empty_unsupported_inventory_cannot_be_relabelled_complete(self) -> None:
        language = LanguageId("ruby")
        binding = self.structural_binding(language.value)
        actual = self.application.generate_map(
            language.value, str(self.contract.binding_root(binding)), self.contract.binding_policy(binding)
        )
        published = next(
            item for item in actual.producer.relationship_capabilities if item.family is RelationshipFamily.MEMBER
        )
        overclaim = RelationshipCoverage(
            family=published.family,
            evidence_requirements=published.evidence_requirements,
            semantics=published.semantics,
            semantics_explanation=published.semantics_explanation,
            inventory=CapabilityStatus.SUPPORTED,
            inventory_explanation=published.inventory_explanation,
        )
        payload = actual.model_dump_json().replace(published.model_dump_json(), overclaim.model_dump_json(), 1)
        findings = self.contract.evaluate_binding(
            self.application, language, CodeMap.model_validate_json(payload), binding
        )
        assert any(Discrepancy.FALSE_COMPLETENESS in result.discrepancies for result in findings)
        assert any(Discrepancy.FALSE_SUPPORT in result.discrepancies for result in findings)

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
        index.write_text(original_index.replace("schema_version: 2", "schema_version: 3", 1), encoding="utf-8")

        with pytest.raises(ValidationError, match="schema_version"):
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
            with pytest.raises((RuntimeContractError, ValidationError)):
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

    def test_type_slot_presence_never_accepts_absent_or_unsupported_types(self) -> None:
        for language, scenario in self.contract.scenario_cases():
            for wrapped in scenario.claims:
                claim = wrapped.root
                if claim.observation.root.kind is not ObservationKind.TYPE_SLOT or claim.state is claim.state.PRESENT:
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
            if self.contract.matrix.catalog.expected[binding.scenario].root.kind is ScenarioKind.SOURCE_FACTS:
                continue
            key = (language.value, binding.fixture.root.value.as_posix())
            extracted[key] = self.application.generate_map(
                language.value,
                str(self.contract.binding_root(binding)),
                self.contract.binding_policy(binding),
            )
            assert all(
                result.satisfied
                for result in self.contract.evaluate_binding(self.application, language, extracted[key], binding)
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

    def test_every_published_producer_matches_the_registered_language_contract(self) -> None:
        extracted = {
            language: self.application.generate_map(
                language.value,
                str(self.repository / projection.fixture.root.value),
                self.configured_scan_policy(("ignored/**",), False),
            )
            for language, projection in self.contract.projection_cases()
        }

        for language, code_map in extracted.items():
            assert self.contract.evaluate_producer(self.application, language, code_map).satisfied, language.value

    def test_every_language_exactly_projects_to_the_common_reference_code_map(self) -> None:
        for language, projection in self.contract.projection_cases():
            actual = self.application.generate_map(
                language.value,
                str(self.repository / projection.fixture.root.value),
                self.configured_scan_policy(("ignored/**",), False),
            )

            assert (
                self.contract.project_reference(self.application, actual, projection)
                == self.contract.matrix.reference_code_map
            ), language.value
