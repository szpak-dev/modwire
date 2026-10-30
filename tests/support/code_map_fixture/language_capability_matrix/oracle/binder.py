from dataclasses import dataclass

from modwire.application import FileId

from ..contracts.coverage.contract import LanguageContract
from ..contracts.fixtures.source_set import FixtureSourceSet
from ..projections.mappings.source import SourceIdentityProjection
from ..projections.reference_projection import ReferenceProjection
from ..values.paths.path import RepositoryPath
from ..values.paths.source_path import RepositorySourcePath
from .binding import LanguageScenarioBinding
from .catalog import FixtureScenarioCatalog
from .disposition import ScenarioDisposition
from .document import ScenarioBindingDocument
from .expectation import ScenarioFactExpectation
from .projection import ScenarioProjectionKind


@dataclass(frozen=True)
class FixtureScenarioBinder:
    catalog: FixtureScenarioCatalog

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
        return self.bind(document, fixture, document.mappings, ScenarioProjectionKind.SOURCE_IDENTITIES)

    def bind_reference(self, projection: ReferenceProjection) -> LanguageScenarioBinding:
        return self.bind(
            projection.reference,
            projection.fixture,
            projection.mappings.sources,
            ScenarioProjectionKind.COMMON_REFERENCE,
        )

    def bind(
        self,
        disposition: ScenarioDisposition,
        fixture: FixtureSourceSet,
        mappings: tuple[SourceIdentityProjection, ...],
        projection: ScenarioProjectionKind,
    ) -> LanguageScenarioBinding:
        if disposition.scenario not in self.catalog.scenarios:
            raise ValueError(f"unknown canonical scenario: {disposition.scenario.value}")
        scenario = self.catalog.scenarios[disposition.scenario]
        targets = {FileId(mapping.canonical.value.as_posix()) for mapping in mappings}
        if not targets <= set(scenario.sources):
            raise ValueError(f"{disposition.scenario.value} binding names unknown canonical sources")
        return LanguageScenarioBinding(
            scenario=disposition.scenario,
            fixture=fixture,
            mappings=mappings,
            projection=projection,
            expectations=tuple(
                ScenarioFactExpectation(fact=fact, state=disposition.state, evidence=disposition.evidence)
                for fact in scenario.facts
                if fact.source_id() in targets
            ),
        )
