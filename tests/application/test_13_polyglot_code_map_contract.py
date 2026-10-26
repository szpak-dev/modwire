from modwire.application import CapabilityStatus, CodeMap

from ..support.code_map_fixture import (
    FixtureCapabilityEvidence,
    FixtureCodeMapProjector,
    FixtureProjectionDisposition,
    PolyglotFixtureContract,
)
from .base_test import ApplicationTestCase


class TestPolyglotCodeMapContract(ApplicationTestCase):
    def test_every_fixture_family_has_the_complete_language_inventory(self) -> None:
        fixture = self.repository / "tests/fixtures"
        contract = PolyglotFixtureContract()
        occurrence_languages = contract.languages(fixture / "call_occurrences")
        reference_languages = contract.languages(fixture / "code_map/reference_shop/languages")
        extension_languages = contract.languages(fixture / "code_map/language_extensions")
        registered_languages = self.application.extraction.supported_languages()

        assert occurrence_languages == reference_languages == extension_languages
        assert set(registered_languages) <= set(reference_languages)

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

    def test_registered_fixture_sources_use_catalogued_extensions(self) -> None:
        fixture = self.repository / "tests/fixtures"
        contract = PolyglotFixtureContract()

        for language in self.application.extraction.supported_languages():
            extensions = self.application.extraction.request(language, str(fixture)).runtime.file_extensions
            extension_fixture = fixture / "code_map/language_extensions" / language
            roots = (
                fixture / "call_occurrences" / language,
                fixture / "code_map/reference_shop/languages" / language,
                extension_fixture,
            )
            for root in roots:
                paths = contract.source_paths(root)
                assert paths
                assert all(any(path.endswith(extension) for extension in extensions) for path in paths)
            assert {
                extension
                for extension in extensions
                if any(path.endswith(extension) for path in contract.source_paths(extension_fixture))
            } == set(extensions)

    def test_reference_sources_follow_the_shared_scenario_inventory(self) -> None:
        fixture = self.repository / "tests/fixtures/code_map/reference_shop"
        contract = PolyglotFixtureContract()
        languages = contract.languages(fixture / "languages")
        layouts = {language: contract.source_layout(fixture / "languages" / language) for language in languages}

        assert layouts
        assert len(set(layouts.values())) == 1

    def test_registered_reference_projects_match_the_master_code_map(self) -> None:
        fixture = self.repository / "tests/fixtures/code_map/reference_shop"
        master = CodeMap.model_validate_json((fixture / "expected_code_map.json").read_text(encoding="utf-8"))
        for language in self.application.extraction.supported_languages():
            code_map = self.application.generate_queryable_map(
                language,
                str(fixture / "languages" / language),
                self.configured_scan_policy(("ignored/**",), False),
            )

            assert FixtureCodeMapProjector().project(code_map.code_map) == master, language

    def test_language_extensions_exercise_every_claimed_capability(self) -> None:
        fixtures = self.repository / "tests/fixtures/code_map/language_extensions"
        for language in self.application.extraction.supported_languages():
            code_map = self.application.generate_map(language, str(fixtures / language), self.scan_policy())
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

            assert evidence.capabilities(code_map) == claimed_capabilities, language
            assert evidence.relationships(code_map) == claimed_relationships, language
