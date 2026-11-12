from pathlib import PurePosixPath
from typing import Self

from pydantic import model_validator

from modwire.application import CodeMap, FactCapability, FileId, RelationshipFamily

from ..claim_evaluator import FixtureClaimEvaluator
from ..conclusion import Conclusion
from ..fixture_model import FixtureModel
from ..scenario_contract_error import ScenarioContractError
from ..scenario_violation import ScenarioViolation
from .bundle import LanguageCapabilityBundle
from .contracts.coverage.capability import CapabilityExpectation
from .contracts.coverage.relationship import RelationshipExpectation
from .contracts.manifests.scenario import ManifestScenario
from .documents.index import LanguageCapabilityIndex
from .oracle.binding import LanguageScenarioBinding
from .oracle.catalog import FixtureScenarioCatalog
from .oracle.fixtures.capability import CapabilityFixtureReference
from .oracle.fixtures.manifest import ManifestFixtureReference
from .oracle.fixtures.reference import ScenarioFixtureReference
from .oracle.projection import ScenarioProjectionKind
from .oracle.reference import FixtureFactReference
from .projections.mappings.identity import DeclarationIdentityKey
from .values.enums.fixture_reference_kind import FixtureReferenceKind
from .values.enums.observation_kind import ObservationKind
from .values.names.language_id import LanguageId


class LanguageCapabilityMatrix(FixtureModel):
    index: LanguageCapabilityIndex
    catalog: FixtureScenarioCatalog
    languages: dict[LanguageId, LanguageCapabilityBundle]

    @property
    def reference_code_map(self) -> CodeMap:
        return self.catalog.code_map(self.index.reference_scenario)

    def capability_cases(self) -> tuple[tuple[LanguageId, FactCapability, CapabilityExpectation], ...]:
        return tuple(
            (
                (language, capability, expectation)
                for language, bundle in self.languages.items()
                for capability, expectation in bundle.contract.capabilities.items()
            )
        )

    def relationship_cases(self) -> tuple[tuple[LanguageId, RelationshipFamily, RelationshipExpectation], ...]:
        return tuple(
            (
                (language, relationship, expectation)
                for language, bundle in self.languages.items()
                for relationship, expectation in bundle.contract.relationships.items()
            )
        )

    @model_validator(mode="after")
    def validate_complete_graph(self) -> Self:
        if tuple(self.languages) != tuple(self.index.languages):
            raise ValueError("language bundles do not exactly match the root index")
        self.validate_language_pairs()
        self.validate_manifest_layouts()
        self.validate_projection_targets()
        self.validate_scenario_bindings()
        self.validate_complete_fact_bindings()
        self.validate_claim_targets()
        self.validate_manifest_parameter_targets()
        self.validate_fixture_collections()
        if set(self.catalog.obligations) != set(Conclusion) - {Conclusion.CONTRACT}:
            raise ScenarioContractError(ScenarioViolation.OBLIGATION_COVERAGE, "C01-C12")
        for conclusion, obligation in self.catalog.obligations.items():
            if set(obligation.languages) != set(self.languages):
                raise ScenarioContractError(ScenarioViolation.OBLIGATION_COVERAGE, conclusion.value)
            for language, applicability in obligation.languages.items():
                native_scenarios = {
                    binding.scenario.value
                    for binding in self.languages[language].scenarios
                    if binding.projection is ScenarioProjectionKind.SOURCE_IDENTITIES
                }
                if not {scenario.value for scenario in applicability.evidence} <= native_scenarios:
                    raise ScenarioContractError(ScenarioViolation.UNKNOWN_EVIDENCE, conclusion.value)
        return self

    def fixture_paths(self) -> tuple[PurePosixPath, ...]:
        return (
            *(
                binding.fixture.root.value / source.value
                for bundle in self.languages.values()
                for binding in bundle.scenarios
                for source in binding.fixture.sources
            ),
            *(
                collection.root.value / resource.value
                for collection in self.index.fixture_collections
                for resource in collection.resources
            ),
        )

    def validate_fixture_collections(self) -> None:
        paths = self.fixture_paths()
        suffixes = {
            suffix.value for bundle in self.languages.values() for suffix in bundle.contract.fixtures.source_suffixes
        }
        if any(
            resource.value.suffix in suffixes
            for collection in self.index.fixture_collections
            for resource in collection.resources
        ):
            raise ValueError("language source files must belong to scenario bindings, not fixture resources")
        if len(set(paths)) != len(paths):
            raise ValueError("fixture files must have exactly one binding or resource owner")
        for path in paths:
            if sum(path.is_relative_to(collection.root.value) for collection in self.index.fixture_collections) != 1:
                raise ValueError("every fixture file must belong to one declared collection")
        for collection in self.index.fixture_collections:
            if not any(
                binding.fixture.root.value.is_relative_to(collection.root.value)
                for bundle in self.languages.values()
                for binding in bundle.scenarios
            ):
                raise ValueError("fixture collections must own bound sources")

    def manifest_binding(self, language: LanguageId, scenario: ManifestScenario) -> LanguageScenarioBinding:
        bundle = self.languages[language]
        reference = ScenarioFixtureReference(
            ManifestFixtureReference(kind=FixtureReferenceKind.MANIFEST, scenario=scenario.name)
        )
        document = next(document for document in bundle.reference_projection.scenarios if document.fixture == reference)
        return next(binding for binding in bundle.scenarios if binding.scenario == document.scenario)

    def validate_manifest_parameter_targets(self) -> None:
        evaluator = FixtureClaimEvaluator()
        for language, bundle in self.languages.items():
            for scenario in bundle.contract.manifests.scenarios:
                binding = self.manifest_binding(language, scenario)
                source = binding.expected_source(
                    self.catalog.code_map(binding.scenario),
                    FileId(scenario.source.value.relative_to(scenario.name.value).as_posix()),
                )
                for claim in scenario.claims:
                    observation = claim.observation.root
                    if observation.kind is ObservationKind.PARAMETER:
                        present = bool(evaluator.parameters(source, observation.owner.value, observation.position.root))
                        if not evaluator.result(present, claim.state).satisfied:
                            raise ValueError("manifest parameter selector contradicts its canonical source")

    def validate_language_pairs(self) -> None:
        for language, bundle in self.languages.items():
            if bundle.contract.language != language:
                raise ValueError(f"{language.value} contract declares {bundle.contract.language.value}")
            if bundle.reference_projection.language != language:
                raise ValueError(
                    f"{language.value} reference projection declares {bundle.reference_projection.language.value}"
                )

    def validate_scenario_bindings(self) -> None:
        layouts: set[frozenset[tuple[ScenarioFixtureReference, str]]] = set()
        for language, bundle in self.languages.items():
            names = tuple(binding.scenario for binding in bundle.scenarios)
            if len(set(names)) != len(names) or set(names) != set(self.catalog.scenarios):
                raise ValueError(f"{language.value} bindings must cover every canonical scenario exactly once")
            references = tuple(document.fixture for document in bundle.reference_projection.scenarios)
            expected = {
                *(
                    ScenarioFixtureReference(
                        CapabilityFixtureReference(kind=FixtureReferenceKind.CAPABILITY, role=role)
                    )
                    for role in bundle.contract.fixtures.source_sets()
                ),
                *(
                    ScenarioFixtureReference(
                        ManifestFixtureReference(kind=FixtureReferenceKind.MANIFEST, scenario=scenario.name)
                    )
                    for scenario in bundle.contract.manifests.scenarios
                ),
            }
            if len(set(references)) != len(references) or set(references) != expected:
                raise ValueError(f"{language.value} bindings must own every fixture family and manifest scenario")
            layouts.add(
                frozenset(
                    (document.fixture, document.scenario.value) for document in bundle.reference_projection.scenarios
                )
            )
        if len(layouts) != 1:
            raise ValueError("language bindings must share one canonical fixture-scenario layout")

    def validate_complete_fact_bindings(self) -> None:
        for name, scenario in self.catalog.scenarios.items():
            covered: set[FixtureFactReference] = set()
            for bundle in self.languages.values():
                binding = next(binding for binding in bundle.scenarios if binding.scenario == name)
                targets = {mapping.canonical.value.as_posix() for mapping in binding.mappings}
                expected = {fact for fact in scenario.facts if str(fact.source_id()) in targets}
                actual = binding.facts
                if len(set(actual)) != len(actual) or set(actual) != expected:
                    raise ValueError(f"{name.value} binding must own every selected canonical fact exactly once")
                covered.update(actual)
            if covered != set(scenario.facts):
                raise ValueError(f"{name.value} canonical facts contain an unbound variant")

    def validate_claim_targets(self) -> None:
        evaluator = FixtureClaimEvaluator()
        for language, bundle in self.languages.items():
            for scenario in bundle.contract.scenarios:
                fixture = bundle.contract.fixtures.source_sets()[scenario.fixture]
                binding = next(
                    binding
                    for binding in bundle.scenarios
                    if binding.projection is ScenarioProjectionKind.SOURCE_IDENTITIES and binding.fixture == fixture
                )
                expected = binding.expected_source(
                    self.catalog.code_map(binding.scenario), FileId(scenario.source.value.as_posix())
                )
                for wrapped in scenario.claims:
                    claim = wrapped.root
                    if not evaluator.evaluate_observation(expected, claim.observation, claim.state, expected).satisfied:
                        raise ValueError(f"{language.value}:{scenario.name.value} claim contradicts the common CodeMap")

    def validate_manifest_layouts(self) -> None:
        manifest_layouts: set[tuple[tuple[str, PurePosixPath], ...]] = set()
        for bundle in self.languages.values():
            contract = bundle.contract
            manifest_layouts.add(
                tuple((scenario.name.value, scenario.source.value.parent) for scenario in contract.manifests.scenarios)
            )
        if len(manifest_layouts) != 1:
            raise ValueError("language manifest contracts do not share one scenario layout")

    def validate_projection_targets(self) -> None:
        reference_sources = set(self.reference_code_map.extraction.files)
        reference_declarations = {
            DeclarationIdentityKey(declaration.declaration_id)
            for source in self.reference_code_map.extraction.files.values()
            for declaration in source.declarations
        }
        reference_callables = {
            DeclarationIdentityKey(callable_fact.declaration_id)
            for source in self.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
        }
        reference_parameters = {
            (DeclarationIdentityKey(callable_fact.declaration_id), parameter.name)
            for source in self.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
            for parameter in callable_fact.parameters
        }
        for bundle in self.languages.values():
            projection = bundle.reference_projection
            suffixes = {suffix.value for suffix in bundle.contract.fixtures.source_suffixes}
            if {source.value.suffix for source in projection.fixture.sources} - suffixes:
                raise ValueError(f"{projection.language.value} reference fixture uses an undeclared suffix")
            authored_sources = {item.authored.value for item in projection.mappings.sources}
            excluded_sources = {
                source.value for source in projection.fixture.sources if source.value not in authored_sources
            }
            excluded_patterns = self.reference_code_map.extraction.manifest.policy.excluded_patterns
            if any(not any(source.match(pattern) for pattern in excluded_patterns) for source in excluded_sources):
                raise ValueError(f"{projection.language.value} projection leaves an included source unmapped")
            if {item.canonical.value.as_posix() for item in projection.mappings.sources} != reference_sources:
                raise ValueError(f"{projection.language.value} projection source targets differ from reference")
            if {
                DeclarationIdentityKey(item.canonical) for item in projection.mappings.declarations
            } != reference_declarations:
                raise ValueError(f"{projection.language.value} declaration targets differ from reference")
            if {
                DeclarationIdentityKey(item.canonical) for item in projection.mappings.callables
            } != reference_callables:
                raise ValueError(f"{projection.language.value} callable targets differ from reference")
            if projection.canonical_parameters != reference_parameters:
                raise ValueError(f"{projection.language.value} parameter targets differ from reference")
