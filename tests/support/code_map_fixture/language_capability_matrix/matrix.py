from pathlib import PurePosixPath
from typing import Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus, FactCapability, RelationshipFamily

from ..model import FixtureModel
from .expectations.capability import CapabilityExpectation
from .expectations.manifest import ManifestEvidenceExpectation
from .expectations.parameter_kind import ParameterKindExpectation
from .expectations.relationship import RelationshipExpectation
from .expectations.scenario import LimitationScenarioExpectation
from .expectations.transition import ManifestTransitionExpectation
from .row import LanguageCapabilityRow


class LanguageCapabilityMatrix(FixtureModel):
    reference_projection: str = Field(min_length=1)
    parameter_kinds: tuple[str, ...] = Field(min_length=1)
    manifest_transitions: tuple[ManifestTransitionExpectation, ...]
    languages: dict[str, LanguageCapabilityRow]

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
        if len(set(self.parameter_kinds)) != len(self.parameter_kinds):
            raise ValueError("parameter-kind vocabulary contains duplicates")
        if any(
            all(kind not in row.parameter_kinds.present for row in self.languages.values())
            for kind in self.parameter_kinds
        ):
            raise ValueError("parameter-kind vocabulary contains a kind absent from every language")
        manifest_layouts: set[tuple[str, ...]] = set()
        for language, row in self.languages.items():
            self.validate_row_inventory(language, row)
            self.validate_row_scenarios(language, row)
            if set((*row.parameter_kinds.present, *row.parameter_kinds.not_applicable)) != set(
                self.parameter_kinds
            ):
                raise ValueError(f"{language} parameter kinds do not partition the matrix vocabulary")
            if not row.convention.accepts_source_path(row.parameter_kinds.source):
                raise ValueError(f"{language} parameter-kind evidence is not a source path")
            if not all(row.convention.accepts_source_path(path) for path in row.fixtures.manifest_sources.values()):
                raise ValueError(f"{language} manifest inventory contains a non-source path")
            if not all(
                row.convention.accepts_source_path(path)
                for path in row.fixtures.type_reference_sources()
            ):
                raise ValueError(f"{language} type-reference inventory contains a non-source path")
            type_reference_roots = {
                PurePosixPath(path).parents[1]
                for path in row.fixtures.type_reference_sources()
            }
            if len(type_reference_roots) != 1:
                raise ValueError(f"{language} type-reference sources do not share one language root")
            if any(
                PurePosixPath(path).parts[0] != scenario for scenario, path in row.fixtures.manifest_sources.items()
            ):
                raise ValueError(f"{language} manifest source is outside its named scenario")
            if tuple(row.manifest_expectations) != tuple(row.fixtures.manifest_sources):
                raise ValueError(f"{language} manifest expectations do not exactly cover fixture scenarios")
            if any(
                expectation.source != row.fixtures.manifest_sources[scenario]
                for scenario, expectation in row.manifest_expectations.items()
            ):
                raise ValueError(f"{language} manifest expectation source differs from fixture inventory")
            manifest_layouts.add(
                tuple(
                    f"{scenario}:{PurePosixPath(path).parent.as_posix()}"
                    for scenario, path in row.fixtures.manifest_sources.items()
                )
            )
        if len(manifest_layouts) != 1:
            raise ValueError("language manifest inventories do not share one scenario layout")
        manifest_scenarios = tuple(next(iter(self.languages.values())).fixtures.manifest_sources)
        if any(
            transition.before not in manifest_scenarios or transition.after not in manifest_scenarios
            for transition in self.manifest_transitions
        ):
            raise ValueError("manifest transition names an undeclared scenario")
        return self

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
