import pytest

from modwire.application import CapabilityStatus, CodeMap

from ..support.code_map_fixture import (
    FixtureCapabilityEvidence,
    FixtureCodeMapProjector,
    FixtureLanguageConvention,
    FixtureProjectionDisposition,
    PolyglotFixtureContract,
)
from .base_test import ApplicationTestCase

REGISTERED_CONVENTIONS = (
    FixtureLanguageConvention.PYTHON,
    FixtureLanguageConvention.TYPESCRIPT,
    FixtureLanguageConvention.PHP,
    FixtureLanguageConvention.JAVA,
)


class TestPolyglotCodeMapContract(ApplicationTestCase):
    def test_every_fixture_family_has_the_complete_language_inventory(self) -> None:
        fixture = self.repository / "tests/fixtures"
        expected = tuple(sorted(convention.language for convention in FixtureLanguageConvention))
        contract = PolyglotFixtureContract()

        assert contract.languages(fixture / "call_occurrences") == expected
        assert contract.languages(fixture / "code_map/reference_shop/languages") == expected
        assert contract.languages(fixture / "code_map/language_extensions") == expected

    def test_projector_classifies_every_field_it_can_transform(self) -> None:
        fixture = self.repository / "tests/fixtures/code_map/reference_shop"
        master = CodeMap.model_validate_json((fixture / "expected_code_map.json").read_text(encoding="utf-8"))
        policy = FixtureCodeMapProjector().field_policy()
        model_fields = PolyglotFixtureContract().projected_model_fields(master)

        assert policy.keys() == model_fields.keys()
        assert all(frozenset(policy[model_name]) == fields for model_name, fields in model_fields.items())
        assert {disposition for model_policy in policy.values() for disposition in model_policy.values()} == set(
            FixtureProjectionDisposition
        )

    def test_every_fixture_source_uses_the_language_filename_convention(self) -> None:
        fixture = self.repository / "tests/fixtures"
        contract = PolyglotFixtureContract()

        for convention in FixtureLanguageConvention:
            roots = (
                fixture / "call_occurrences" / convention.language,
                fixture / "code_map/reference_shop/languages" / convention.language,
                fixture / "code_map/language_extensions" / convention.language,
            )
            for root in roots:
                paths = contract.source_paths(root)
                assert paths
                assert all(convention.accepts_source_path(path) for path in paths)

    @pytest.mark.parametrize(
        "convention",
        tuple(FixtureLanguageConvention),
        ids=tuple(convention.language for convention in FixtureLanguageConvention),
    )
    def test_reference_sources_follow_the_shared_scenario_inventory(
        self,
        convention: FixtureLanguageConvention,
    ) -> None:
        fixture = self.repository / "tests/fixtures/code_map/reference_shop"
        master = CodeMap.model_validate_json((fixture / "expected_code_map.json").read_text(encoding="utf-8"))
        expected_paths = {
            convention.source_path(str(source_id), source_file.declarations[0].name)
            for source_id, source_file in master.extraction.files.items()
        }
        expected_paths.add(convention.source_path("ignored/generated_order", "GeneratedOrder"))

        project = fixture / "languages" / convention.language
        actual_paths = {source.relative_to(project).as_posix() for source in project.rglob(f"*{convention.suffix}")}

        assert actual_paths == expected_paths

    @pytest.mark.parametrize(
        "convention",
        REGISTERED_CONVENTIONS,
        ids=tuple(convention.language for convention in REGISTERED_CONVENTIONS),
    )
    def test_registered_reference_projects_match_the_master_code_map(
        self,
        convention: FixtureLanguageConvention,
    ) -> None:
        fixture = self.repository / "tests/fixtures/code_map/reference_shop"
        master = CodeMap.model_validate_json((fixture / "expected_code_map.json").read_text(encoding="utf-8"))
        code_map = self.application.generate_queryable_map(
            convention.language,
            str(fixture / "languages" / convention.language),
            self.configured_scan_policy(("ignored/**",), False),
        )

        assert FixtureCodeMapProjector().project(code_map.code_map) == master

    @pytest.mark.parametrize(
        "convention",
        REGISTERED_CONVENTIONS,
        ids=tuple(convention.language for convention in REGISTERED_CONVENTIONS),
    )
    def test_language_extensions_exercise_every_claimed_capability(
        self,
        convention: FixtureLanguageConvention,
    ) -> None:
        fixture = self.repository / "tests/fixtures/code_map/language_extensions" / convention.language
        code_map = self.application.generate_map(convention.language, str(fixture), self.scan_policy())
        evidence = FixtureCapabilityEvidence()
        claimed_capabilities = tuple(
            coverage.capability
            for coverage in code_map.producer.capabilities
            if coverage.status is not CapabilityStatus.UNSUPPORTED
        )
        claimed_relationships = tuple(
            coverage.family
            for coverage in code_map.producer.relationship_capabilities
            if coverage.semantics is not CapabilityStatus.UNSUPPORTED
            or coverage.inventory is not CapabilityStatus.UNSUPPORTED
        )

        assert evidence.capabilities(code_map) == claimed_capabilities
        assert evidence.relationships(code_map) == claimed_relationships
