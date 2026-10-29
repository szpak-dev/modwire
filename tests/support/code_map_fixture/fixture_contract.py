from pathlib import Path

from modwire.application import FactCapability, RelationshipFamily

from .claim_evaluator import FixtureClaimEvaluator
from .fixture_contract_error import FixtureContractError
from .language_capability_matrix.contracts.coverage import CapabilityExpectation, RelationshipExpectation
from .language_capability_matrix.contracts.fixtures import FixtureSourceSet
from .language_capability_matrix.contracts.manifests import ManifestScenario, ManifestTransition
from .language_capability_matrix.contracts.scenarios import CapabilityScenario
from .language_capability_matrix.model import LanguageCapabilityBundle
from .language_capability_matrix.projections.model import ReferenceProjection
from .language_capability_matrix.reader import LanguageCapabilityMatrixReader
from .language_capability_matrix.values import FixtureRole, LanguageId, SourceSuffix
from .projector import FixtureCodeMapProjector


class PolyglotFixtureContract:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self.matrix = LanguageCapabilityMatrixReader().read(repository / "language-capabilities.yaml")
        self.evaluator = FixtureClaimEvaluator()
        self.projector = FixtureCodeMapProjector()

    def capability_cases(
        self,
    ) -> tuple[tuple[LanguageId, FactCapability, CapabilityExpectation], ...]:
        return self.matrix.capability_cases()

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
