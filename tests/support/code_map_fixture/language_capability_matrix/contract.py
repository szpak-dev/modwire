from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus, FactCapability, RelationshipFamily

from ..model import FixtureModel
from .capabilities.coverage import CapabilityExpectation, ParameterKindExpectation
from .capabilities.limitations import LanguageCapabilityLimitations
from .fixtures.inventory import LanguageFixtureInventory
from .fixtures.projection import ReferenceProjection
from .manifests.coverage import ManifestEvidenceExpectation, ManifestTransitionExpectation
from .relationships.coverage import RelationshipExpectation
from .relationships.limitations import LanguageRelationshipLimitations
from .values import RepositoryDocumentPath


class LimitationScenarioExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source: str = Field(min_length=1)
    authored_syntax: tuple[str, ...] = Field(min_length=1)


class LanguageCapabilityIndex(FixtureModel):
    schema_version: Literal[1]
    reference_code_map: RepositoryDocumentPath
    parameter_kinds: tuple[str, ...] = Field(min_length=1)
    manifest_transitions: tuple[ManifestTransitionExpectation, ...] = Field(min_length=1)
    languages: dict[str, RepositoryDocumentPath] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        if any(not language for language in self.languages):
            raise ValueError("language keys must not be empty")
        if len(set(self.parameter_kinds)) != len(self.parameter_kinds):
            raise ValueError("parameter-kind vocabulary contains duplicates")
        paths = tuple(path.value for path in self.languages.values())
        if len(set(paths)) != len(paths):
            raise ValueError("language document paths contain duplicates")
        if any(path.is_absolute() or path.suffix != ".yaml" for path in paths):
            raise ValueError("language document paths must be relative YAML paths")
        if len({path.parent for path in paths}) != 1 or any(len(path.parts) != 2 for path in paths):
            raise ValueError("language documents must share one nested directory")
        if any(path.name != f"{language}.yaml" for language, path in zip(self.languages, paths, strict=True)):
            raise ValueError("language document filenames must match their language keys")
        return self


class LanguageCapabilityRow(FixtureModel):
    language: str = Field(min_length=1)
    fixtures: LanguageFixtureInventory
    projection: ReferenceProjection
    capabilities: dict[FactCapability, CapabilityExpectation]
    relationships: dict[RelationshipFamily, RelationshipExpectation]
    scenarios: tuple[LimitationScenarioExpectation, ...]
    parameter_kinds: ParameterKindExpectation
    manifest_expectations: dict[str, ManifestEvidenceExpectation]
    capability_limitations: LanguageCapabilityLimitations
    relationship_limitations: LanguageRelationshipLimitations


class LanguageCapabilityMatrix(FixtureModel):
    index: LanguageCapabilityIndex
    languages: dict[str, LanguageCapabilityRow]

    @property
    def reference_code_map(self) -> PurePosixPath:
        return self.index.reference_code_map.value

    @property
    def parameter_kinds(self) -> tuple[str, ...]:
        return self.index.parameter_kinds

    @property
    def manifest_transitions(self) -> tuple[ManifestTransitionExpectation, ...]:
        return self.index.manifest_transitions

    def capability_cases(self) -> tuple[tuple[str, FactCapability, CapabilityExpectation], ...]:
        return tuple(
            (language, capability, expectation)
            for language, row in self.languages.items()
            for capability, expectation in row.capabilities.items()
        )

    def relationship_cases(self) -> tuple[tuple[str, RelationshipFamily, RelationshipExpectation], ...]:
        return tuple(
            (language, family, expectation)
            for language, row in self.languages.items()
            for family, expectation in row.relationships.items()
        )

    def scenario_cases(self) -> tuple[tuple[str, LimitationScenarioExpectation], ...]:
        return tuple((language, scenario) for language, row in self.languages.items() for scenario in row.scenarios)

    def parameter_kind_cases(self) -> tuple[tuple[str, ParameterKindExpectation], ...]:
        return tuple((language, row.parameter_kinds) for language, row in self.languages.items())

    def manifest_cases(self) -> tuple[tuple[str, str, ManifestEvidenceExpectation], ...]:
        return tuple(
            (language, scenario, expectation)
            for language, row in self.languages.items()
            for scenario, expectation in row.manifest_expectations.items()
        )

    def manifest_transition_cases(
        self,
    ) -> tuple[tuple[str, LanguageCapabilityRow, ManifestTransitionExpectation], ...]:
        return tuple(
            (language, row, transition)
            for language, row in self.languages.items()
            for transition in self.manifest_transitions
        )

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        if tuple(self.languages) != tuple(self.index.languages):
            raise ValueError("language documents do not exactly match the root index")
        if any(
            all(kind not in row.parameter_kinds.present for row in self.languages.values())
            for kind in self.parameter_kinds
        ):
            raise ValueError("parameter-kind vocabulary contains a kind absent from every language")
        manifest_layouts: set[tuple[str, ...]] = set()
        for language, row in self.languages.items():
            if row.language != language:
                raise ValueError(f"{language} document declares language {row.language}")
            self.validate_row_inventory(language, row)
            self.validate_row_scenarios(language, row)
            if set((*row.parameter_kinds.present, *row.parameter_kinds.not_applicable)) != set(self.parameter_kinds):
                raise ValueError(f"{language} parameter kinds do not partition the matrix vocabulary")
            self.validate_source_suffix_coverage(language, row)
            if any(
                path.value.parts[0] != scenario for scenario, path in row.fixtures.manifests.sources.items()
            ):
                raise ValueError(f"{language} manifest source is outside its named scenario")
            if tuple(row.manifest_expectations) != tuple(row.fixtures.manifests.sources):
                raise ValueError(f"{language} manifest expectations do not exactly cover fixture scenarios")
            if any(
                PurePosixPath(expectation.source) != row.fixtures.manifests.sources[scenario].value
                for scenario, expectation in row.manifest_expectations.items()
            ):
                raise ValueError(f"{language} manifest expectation source differs from fixture inventory")
            manifest_layouts.add(
                tuple(
                    f"{scenario}:{path.value.parent.as_posix()}"
                    for scenario, path in row.fixtures.manifests.sources.items()
                )
            )
        if len(manifest_layouts) != 1:
            raise ValueError("language manifest inventories do not share one scenario layout")
        manifest_scenarios = tuple(next(iter(self.languages.values())).fixtures.manifests.sources)
        if any(
            transition.before not in manifest_scenarios or transition.after not in manifest_scenarios
            for transition in self.manifest_transitions
        ):
            raise ValueError("manifest transition names an undeclared scenario")
        return self

    def validate_source_suffix_coverage(self, language: str, row: LanguageCapabilityRow) -> None:
        suffixes = {suffix.value for suffix in row.fixtures.source_suffixes}
        source_sets = (
            row.fixtures.reference,
            row.fixtures.language_extensions,
            row.fixtures.capability_gaps,
            row.fixtures.parameter_kinds,
        )
        paths = (
            *(source.value for source_set in source_sets for source in source_set.sources),
            row.fixtures.type_references.cases.value,
            row.fixtures.type_references.empty.value,
            *(source.value for source in row.fixtures.manifests.sources.values()),
        )
        observed = {path.suffix for path in paths}
        if observed != suffixes:
            raise ValueError(
                f"{language} source suffix inventory differs: declared {sorted(suffixes)}, observed {sorted(observed)}"
            )

    def validate_row_inventory(self, language: str, row: LanguageCapabilityRow) -> None:
        if tuple(row.capabilities) != tuple(FactCapability):
            raise ValueError(f"{language} does not cover every fact capability in canonical order")
        if tuple(row.relationships) != tuple(RelationshipFamily):
            raise ValueError(f"{language} does not cover every relationship family in canonical order")

    def validate_row_scenarios(self, language: str, row: LanguageCapabilityRow) -> None:
        metadata_scenarios = tuple(scenario.scenario for scenario in row.scenarios)
        if len(set(metadata_scenarios)) != len(metadata_scenarios):
            raise ValueError(f"{language} contains duplicate scenario metadata")

        capability_cases = row.capability_limitations.cases()
        relationship_cases = row.relationship_limitations.cases()
        typed_scenarios = {scenario for scenario, contract_cell in (*capability_cases, *relationship_cases)}
        if typed_scenarios != set(metadata_scenarios):
            raise ValueError(f"{language} scenario metadata does not exactly cover typed limitations")

        capability_scenarios = {
            capability.value: tuple(
                scenario for scenario, contract_cell in capability_cases if contract_cell == capability.value
            )
            for capability in FactCapability
        }
        for capability, expectation in row.capabilities.items():
            self.validate_status_limitations(
                language,
                capability.value,
                expectation.status,
                expectation.limitation_scenarios,
            )
            if expectation.limitation_scenarios != capability_scenarios[capability.value]:
                raise ValueError(f"{language} {capability.value} limitations are not owned by that capability")

        for family, expectation in row.relationships.items():
            semantics_cell = f"{family.value}_semantics"
            inventory_cell = f"{family.value}_inventory"
            semantics_scenarios = tuple(
                scenario for scenario, contract_cell in relationship_cases if contract_cell == semantics_cell
            )
            inventory_scenarios = tuple(
                scenario for scenario, contract_cell in relationship_cases if contract_cell == inventory_cell
            )
            self.validate_status_limitations(
                language,
                f"{family.value} semantics",
                expectation.semantics,
                expectation.semantics_limitation_scenarios,
            )
            self.validate_status_limitations(
                language,
                f"{family.value} inventory",
                expectation.inventory,
                expectation.inventory_limitation_scenarios,
            )
            if expectation.semantics_limitation_scenarios != semantics_scenarios:
                raise ValueError(f"{language} {family.value} semantics limitations are not owned by that cell")
            if expectation.inventory_limitation_scenarios != inventory_scenarios:
                raise ValueError(f"{language} {family.value} inventory limitations are not owned by that cell")

    def validate_status_limitations(
        self,
        language: str,
        subject: str,
        status: CapabilityStatus,
        scenarios: tuple[str, ...],
    ) -> None:
        if status is CapabilityStatus.SUPPORTED and scenarios:
            raise ValueError(f"{language} supported {subject} has limitation scenarios")
        if status is not CapabilityStatus.SUPPORTED and not scenarios:
            raise ValueError(f"{language} non-supported {subject} has no limitation scenario")
