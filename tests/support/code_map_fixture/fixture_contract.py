import hashlib
from pathlib import Path

from modwire.application import (
    CodeMap,
    CodeValidationError,
    ExtractionError,
    FactCapability,
    FileId,
    ImplementationManifest,
    ModwireApplication,
    RelationshipFamily,
    ScanPolicy,
    SourceFile,
)

from .claim_evaluator import FixtureClaimEvaluator
from .claim_result import ClaimResult
from .conclusion import Conclusion
from .discrepancy import Discrepancy
from .fixture_contract_error import FixtureContractError
from .language_capability_matrix.bundle import LanguageCapabilityBundle
from .language_capability_matrix.contracts.coverage.capability import CapabilityExpectation
from .language_capability_matrix.contracts.coverage.relationship import RelationshipExpectation
from .language_capability_matrix.contracts.fixtures.source_set import FixtureSourceSet
from .language_capability_matrix.contracts.manifests.scenario import ManifestScenario
from .language_capability_matrix.contracts.manifests.transition import ManifestTransition
from .language_capability_matrix.contracts.scenarios.capability import CapabilityScenario
from .language_capability_matrix.oracle.binding import LanguageScenarioBinding
from .language_capability_matrix.oracle.identities import FixtureSourceIdentities
from .language_capability_matrix.oracle.projection import ScenarioProjectionKind
from .language_capability_matrix.projections.reference_projection import ReferenceProjection
from .language_capability_matrix.reader import LanguageCapabilityMatrixReader
from .language_capability_matrix.values.enums.fixture_role import FixtureRole
from .language_capability_matrix.values.names.language_id import LanguageId
from .language_capability_matrix.values.names.scenario_id import ScenarioId
from .language_capability_matrix.values.names.source_suffix import SourceSuffix
from .matrix_report import ExtractionMatrixReport
from .projector import FixtureCodeMapProjector
from .runtime_contract import FixtureRuntimeContract
from .runtime_contract_error import RuntimeContractError


class PolyglotFixtureContract:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self.matrix = LanguageCapabilityMatrixReader().read(repository / "language-capabilities.yaml")
        self.evaluator = FixtureClaimEvaluator()
        self.projector = FixtureCodeMapProjector()
        self.runtime = FixtureRuntimeContract(self.matrix)

    def assess(self, application: ModwireApplication, revision: str, workspace_digest: str) -> ExtractionMatrixReport:
        results: dict[LanguageId, dict[ScenarioId, tuple[ClaimResult, ...]]] = {
            language: {} for language in self.matrix.languages
        }
        observations: dict[LanguageId, dict[ScenarioId, CodeMap]] = {language: {} for language in self.matrix.languages}
        equivalence: set[ScenarioId] = set()
        for language in self.matrix.languages:
            try:
                self.runtime.validate_language(application, language, str(self.repository))
            except RuntimeContractError as error:
                results[language][ScenarioId("runtime")] = (
                    ClaimResult(
                        subject=f"{error.runtime}:{error.violation.value}",
                        expected=error.expected,
                        actual=error.actual,
                        discrepancies=(Discrepancy.INVALID_EVIDENCE,),
                        conclusions=(Conclusion.PROVENANCE,),
                        owner_issue=84,
                    ),
                )
        for language, binding in self.scenario_bindings():
            if binding.projection is ScenarioProjectionKind.COMMON_REFERENCE:
                equivalence.add(binding.scenario)
            try:
                code_map = application.generate_map(
                    language.value, str(self.binding_root(binding)), self.binding_policy(binding)
                )
            except (ExtractionError, CodeValidationError) as error:
                results[language][binding.scenario] = (
                    ClaimResult(
                        subject=f"{binding.scenario.value}:{error.code}",
                        expected=self.matrix.catalog.expected[binding.scenario].model_dump_json(),
                        actual=str(error),
                        discrepancies=(Discrepancy.EXTRACTION_FAILURE,),
                        conclusions=tuple(
                            conclusion
                            for conclusion, obligation in self.matrix.catalog.obligations.items()
                            if obligation.languages[language].applicable
                        ),
                        owner_issue=81,
                    ),
                )
                continue
            observations[language][binding.scenario] = code_map
            results[language][binding.scenario] = self.evaluate_binding(application, language, code_map, binding)
        for language, scenario in self.manifest_cases():
            binding = self.matrix.manifest_binding(language, scenario)
            if binding.scenario not in observations[language]:
                continue
            for format in application.implementation_manifest_formats():
                document = application.implementation_manifest(observations[language][binding.scenario], format)
                manifest = application.read_implementation_manifest(document)
                results[language][binding.scenario] += self.evaluate_manifest(manifest, scenario)
        results = self.evaluator.evaluate_obligations(self.matrix.catalog, results, frozenset(equivalence))
        return ExtractionMatrixReport(
            revision=revision,
            workspace_digest=workspace_digest,
            matrix_schema_version=self.matrix.index.schema_version.root,
            runtime_requirements=self.runtime_document(),
            obligations=self.matrix.catalog.obligations,
            results=results,
            observations=observations,
            equivalence_cases=frozenset(equivalence),
            reviewed_gaps=self.matrix.catalog.reviewed_gaps,
        )

    def capability_cases(
        self,
    ) -> tuple[tuple[LanguageId, FactCapability, CapabilityExpectation], ...]:
        return self.matrix.capability_cases()

    def capability_expectation(self, language: str, capability: FactCapability) -> CapabilityExpectation:
        return next(
            expectation
            for candidate, declared_capability, expectation in self.capability_cases()
            if candidate.value == language and declared_capability is capability
        )

    def runtime_document(self) -> str:
        return self.runtime.document()

    def validate_runtime_bindings(self, application: ModwireApplication) -> None:
        self.runtime.validate_bindings(application, str(self.repository))

    def validate_runtime(self, application: ModwireApplication) -> None:
        self.runtime.validate(application, str(self.repository))

    def install_runtime_packages(self) -> None:
        self.runtime.install_packages()

    def relationship_cases(
        self,
    ) -> tuple[tuple[LanguageId, RelationshipFamily, RelationshipExpectation], ...]:
        return self.matrix.relationship_cases()

    def scenario_cases(self) -> tuple[tuple[LanguageId, CapabilityScenario], ...]:
        return tuple(
            (language, scenario)
            for language, bundle in self.matrix.languages.items()
            for scenario in bundle.contract.scenarios
        )

    def manifest_cases(self) -> tuple[tuple[LanguageId, ManifestScenario], ...]:
        return tuple(
            (language, scenario)
            for language, bundle in self.matrix.languages.items()
            for scenario in bundle.contract.manifests.scenarios
        )

    def manifest_transition_cases(
        self,
    ) -> tuple[tuple[LanguageId, LanguageCapabilityBundle, ManifestTransition], ...]:
        return tuple(
            (language, bundle, transition)
            for language, bundle in self.matrix.languages.items()
            for transition in bundle.contract.manifests.transitions
        )

    def projection_cases(self) -> tuple[tuple[LanguageId, ReferenceProjection], ...]:
        return tuple((language, bundle.reference_projection) for language, bundle in self.matrix.languages.items())

    def scenario_bindings(self) -> tuple[tuple[LanguageId, LanguageScenarioBinding], ...]:
        return tuple(
            (language, binding) for language, bundle in self.matrix.languages.items() for binding in bundle.scenarios
        )

    def binding_root(self, binding: LanguageScenarioBinding) -> Path:
        return self.repository / binding.fixture.root.value

    def binding_policy(self, binding: LanguageScenarioBinding) -> ScanPolicy:
        return self.matrix.catalog.policy(binding.scenario)

    def evaluate_binding(
        self,
        application: ModwireApplication,
        language: LanguageId,
        code_map: CodeMap,
        binding: LanguageScenarioBinding,
    ) -> tuple[ClaimResult, ...]:
        producer = self.evaluate_producer(application, language, code_map)
        if binding.projection is ScenarioProjectionKind.COMMON_REFERENCE:
            code_map = self.projector.project(
                code_map, self.matrix.languages[language].reference_projection, self.matrix.reference_code_map
            )
            sources = {
                FileId(mapping.canonical.value.as_posix()): FileId(mapping.canonical.value.as_posix())
                for mapping in binding.mappings
            }
        else:
            sources = {
                FileId(mapping.authored.value.as_posix()): FileId(mapping.canonical.value.as_posix())
                for mapping in binding.mappings
            }
        return (
            producer,
            *self.evaluator.evaluate_binding(code_map, self.matrix.catalog, binding, FixtureSourceIdentities(sources)),
        )

    def evaluate_producer(
        self, application: ModwireApplication, language: LanguageId, code_map: CodeMap
    ) -> ClaimResult:
        descriptor = self.runtime.descriptor(application, language, str(self.repository))
        return self.evaluator.evaluate_producer(code_map.producer, self.matrix.languages[language].contract, descriptor)

    def expected_source(self, language: LanguageId, scenario: CapabilityScenario) -> SourceFile:
        bundle = self.matrix.languages[language]
        fixture = bundle.contract.fixtures.source_sets()[scenario.fixture]
        binding = next(
            binding
            for binding in bundle.scenarios
            if binding.projection is ScenarioProjectionKind.SOURCE_IDENTITIES and binding.fixture == fixture
        )
        return binding.expected_source(
            self.matrix.catalog.code_map(binding.scenario), FileId(scenario.source.value.as_posix())
        )

    def evaluate_scenario(self, code_map: CodeMap, scenario: CapabilityScenario) -> tuple[ClaimResult, ...]:
        source_id = scenario.source.value.as_posix()
        expected = self.expected_source(LanguageId(code_map.language), scenario)
        return tuple(
            self.evaluator.evaluate_code_map(code_map, source_id, claim, expected) for claim in scenario.claims
        )

    def evaluate_manifest(
        self,
        manifest: ImplementationManifest,
        scenario: ManifestScenario,
    ) -> tuple[ClaimResult, ...]:
        language = LanguageId(manifest.producer.extractor.language)
        binding = self.matrix.manifest_binding(language, scenario)
        expected = binding.expected_source(
            self.matrix.catalog.code_map(binding.scenario),
            FileId(scenario.source.value.relative_to(scenario.name.value).as_posix()),
        )
        return tuple(self.evaluator.evaluate_manifest(manifest, claim, expected) for claim in scenario.claims)

    def manifest_facts_digest(self, manifest: ImplementationManifest) -> str:
        facts = manifest.model_dump_json(exclude={"producer", "source_manifest"})
        return hashlib.sha256(facts.encode("utf-8")).hexdigest()

    def manifest_root(self, language: LanguageId, scenario: ManifestScenario) -> Path:
        root = self.matrix.languages[language].contract.manifests.root.value
        return self.repository / root / scenario.name.value

    def project_reference(
        self, application: ModwireApplication, code_map: CodeMap, projection: ReferenceProjection
    ) -> CodeMap:
        if not self.evaluate_producer(application, projection.language, code_map).satisfied:
            raise FixtureContractError("reference projection producer differs from its registered language contract")
        return self.projector.project(code_map, projection, self.matrix.reference_code_map)

    def fixture_root(self, language: LanguageId, role: FixtureRole) -> Path:
        fixtures = self.matrix.languages[language].contract.fixtures
        return self.repository / fixtures.source_sets()[role].root.value

    def validate_inventories(self) -> None:
        paths = self.matrix.fixture_paths()
        for collection in self.matrix.index.fixture_collections:
            root = self.repository / collection.root.value
            expected_files = {self.repository / path for path in paths if path.is_relative_to(collection.root.value)}
            expected = expected_files | {
                parent
                for path in expected_files
                for parent in path.parents
                if parent != root and parent.is_relative_to(root)
            }
            if not root.is_dir() or set(root.rglob("*")) != expected:
                raise FixtureContractError(f"fixture collection inventory differs from its complete bindings: {root}")
        for bundle in self.matrix.languages.values():
            contract = bundle.contract
            for fixture in contract.fixtures.source_sets().values():
                self.validate_source_suffixes(fixture, contract.fixtures.source_suffixes)

    def validate_source_suffixes(
        self,
        fixture: FixtureSourceSet,
        suffixes: tuple[SourceSuffix, ...],
    ) -> None:
        accepted = {suffix.value for suffix in suffixes}
        observed = {source.value.suffix for source in fixture.sources}
        unexpected = tuple(sorted(observed - accepted))
        if unexpected:
            raise FixtureContractError(f"source suffix mismatch: unexpected {unexpected}")
