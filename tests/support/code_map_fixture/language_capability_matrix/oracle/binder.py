from dataclasses import dataclass

from modwire.application import FileId

from ..contracts.coverage.contract import LanguageContract
from ..contracts.fixtures.source_set import FixtureSourceSet
from ..projections.mappings.source import SourceIdentityProjection
from ..projections.reference_projection import ReferenceProjection
from ..values.names.scenario_id import ScenarioId
from ..values.paths.path import RepositoryPath
from ..values.paths.source_path import RepositorySourcePath
from .binding import LanguageScenarioBinding
from .catalog import FixtureScenarioCatalog
from .document import ScenarioBindingDocument
from .projection import ScenarioProjectionKind


@dataclass(frozen=True)
class FixtureScenarioBinder:
    catalog: FixtureScenarioCatalog
    reference_scenario: ScenarioId

    def bind_document(self, contract: LanguageContract, document: ScenarioBindingDocument) -> LanguageScenarioBinding:
        reference = document.fixture.root
        if reference.kind == "capability":
            fixture = contract.fixtures.source_sets()[reference.role]
        else:
            scenario = next(item for item in contract.manifests.scenarios if item.name == reference.scenario)
            fixture = FixtureSourceSet(
                root=RepositoryPath(contract.manifests.root.value / scenario.name.value),
                sources=(RepositorySourcePath(scenario.source.value.relative_to(scenario.name.value)),),
            )
        return self.bind(document.scenario, fixture, document.mappings, ScenarioProjectionKind.SOURCE_IDENTITIES)

    def bind_reference(self, projection: ReferenceProjection) -> LanguageScenarioBinding:
        return self.bind(
            self.reference_scenario,
            projection.fixture,
            projection.mappings.sources,
            ScenarioProjectionKind.COMMON_REFERENCE,
        )

    def bind(
        self,
        name: ScenarioId,
        fixture: FixtureSourceSet,
        mappings: tuple[SourceIdentityProjection, ...],
        projection: ScenarioProjectionKind,
    ) -> LanguageScenarioBinding:
        if name not in self.catalog.scenarios:
            raise ValueError(f"unknown canonical scenario: {name.value}")
        scenario = self.catalog.scenarios[name]
        targets = {FileId(mapping.canonical.value.as_posix()) for mapping in mappings}
        if not targets <= set(scenario.sources):
            raise ValueError(f"{name.value} binding names unknown canonical sources")
        return LanguageScenarioBinding(
            scenario=name,
            fixture=fixture,
            mappings=mappings,
            projection=projection,
            facts=tuple(fact for fact in scenario.facts if fact.source_id() in targets),
        )
