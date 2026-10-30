import hashlib
from pathlib import Path

from modwire.application import CodeMap, FactCapability, ImplementationManifest, ModwireApplication, RelationshipFamily

from .claim_evaluator import FixtureClaimEvaluator
from .claim_result import ClaimResult
from .fixture_contract_error import FixtureContractError
from .language_capability_matrix.bundle import LanguageCapabilityBundle
from .language_capability_matrix.contracts.coverage.capability import CapabilityExpectation
from .language_capability_matrix.contracts.coverage.relationship import RelationshipExpectation
from .language_capability_matrix.contracts.fixtures.source_set import FixtureSourceSet
from .language_capability_matrix.contracts.manifests.scenario import ManifestScenario
from .language_capability_matrix.contracts.manifests.transition import ManifestTransition
from .language_capability_matrix.contracts.scenarios.capability import CapabilityScenario
from .language_capability_matrix.projections.reference_projection import ReferenceProjection
from .language_capability_matrix.reader import LanguageCapabilityMatrixReader
from .language_capability_matrix.values.enums.fixture_role import FixtureRole
from .language_capability_matrix.values.names.language_id import LanguageId
from .language_capability_matrix.values.names.source_suffix import SourceSuffix
from .projector import FixtureCodeMapProjector
from .runtime_contract import FixtureRuntimeContract


class PolyglotFixtureContract:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self.matrix = LanguageCapabilityMatrixReader().read(repository / "language-capabilities.yaml")
        self.evaluator = FixtureClaimEvaluator()
        self.projector = FixtureCodeMapProjector()
        self.runtime = FixtureRuntimeContract(self.matrix)

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

    def evaluate_scenario(self, code_map: CodeMap, scenario: CapabilityScenario) -> tuple[ClaimResult, ...]:
        source_id = scenario.source.value.as_posix()
        return tuple(self.evaluator.evaluate_code_map(code_map, source_id, claim) for claim in scenario.claims)

    def evaluate_manifest(
        self,
        manifest: ImplementationManifest,
        scenario: ManifestScenario,
    ) -> tuple[ClaimResult, ...]:
        return tuple(self.evaluator.evaluate_manifest(manifest, claim) for claim in scenario.claims)

    def manifest_facts_digest(self, manifest: ImplementationManifest) -> str:
        facts = manifest.model_dump_json(exclude={"producer", "source_manifest"})
        return hashlib.sha256(facts.encode("utf-8")).hexdigest()

    def manifest_root(self, language: LanguageId, scenario: ManifestScenario) -> Path:
        root = self.matrix.languages[language].contract.manifests.root.value
        return self.repository / root / scenario.name.value

    def project_reference(self, code_map: CodeMap, projection: ReferenceProjection) -> CodeMap:
        return self.projector.project(code_map, projection, self.matrix.reference_code_map)

    def fixture_root(self, language: LanguageId, role: FixtureRole) -> Path:
        fixtures = self.matrix.languages[language].contract.fixtures
        roots = {
            FixtureRole.EXTENSIONS: fixtures.extensions.root,
            FixtureRole.GAPS: fixtures.gaps.root,
            FixtureRole.TYPES: fixtures.types.root,
            FixtureRole.PARAMETERS: fixtures.parameters.root,
        }
        return self.repository / roots[role].value

    def validate_inventories(self) -> None:
        for bundle in self.matrix.languages.values():
            contract = bundle.contract
            projection = bundle.reference_projection
            for fixture in (
                contract.fixtures.extensions,
                contract.fixtures.gaps,
                contract.fixtures.types,
                contract.fixtures.parameters,
            ):
                self.validate_source_set(fixture)
                self.validate_source_suffixes(fixture, contract.fixtures.source_suffixes)
            self.validate_source_inventory(
                self.repository / contract.manifests.root.value,
                tuple(scenario.source.value.as_posix() for scenario in contract.manifests.scenarios),
            )
            self.validate_source_inventory(
                self.repository / projection.fixture.root.value,
                tuple(source.value.as_posix() for source in projection.fixture.sources),
            )

    def languages(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.name for path in root.iterdir() if path.is_dir()))

    def source_paths(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))

    def validate_language_inventory(self, root: Path, expected: tuple[str, ...]) -> None:
        actual = self.languages(root)
        if actual != expected:
            raise FixtureContractError(f"language inventory mismatch: expected {expected}, observed {actual}")

    def validate_source_inventory(self, root: Path, expected: tuple[str, ...]) -> None:
        actual = self.source_paths(root)
        if actual != tuple(sorted(expected)):
            raise FixtureContractError(f"source inventory mismatch: expected {expected}, observed {actual}")

    def validate_source_set(self, fixture: FixtureSourceSet) -> None:
        self.validate_source_inventory(
            self.repository / fixture.root.value,
            tuple(source.value.as_posix() for source in fixture.sources),
        )

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
