from functools import cached_property
from typing import Self

from pydantic import Field, model_validator

from modwire.application import CodeMap, FileId

from ...fixture_model import FixtureModel
from ..values.names.scenario_id import ScenarioId
from ..values.paths.document_path import RepositoryDocumentPath
from .ownership import FixtureSourceOwnership
from .reference import FixtureFactReference
from .scenario import CanonicalFixtureScenario
from .selectors.dependencies import DependencySelector
from .selectors.parameters import ParameterListSelector
from .selectors.selector import ScenarioFactSelector
from .selectors.source import SourceFileSelector


class FixtureScenarioCatalog(FixtureModel):
    expected: dict[ScenarioId, CodeMap] = Field(min_length=1)
    source_documents: dict[ScenarioId, dict[FileId, RepositoryDocumentPath]]

    @cached_property
    def scenarios(self) -> dict[ScenarioId, CanonicalFixtureScenario]:
        return {
            name: CanonicalFixtureScenario(
                sources=tuple(code_map.extraction.files),
                facts=tuple(
                    FixtureFactReference(selector=ScenarioFactSelector(selector))
                    for source in code_map.extraction.files.values()
                    for selector in (
                        SourceFileSelector(kind="source_file", source=source.file_id),
                        DependencySelector(kind="dependencies", source=source.file_id),
                        *(
                            ParameterListSelector(kind="parameter_list", callable=callable_.declaration_id)
                            for callable_ in source.canonical_callables()
                        ),
                    )
                ),
            )
            for name, code_map in self.expected.items()
        }

    @model_validator(mode="after")
    def validate_source_ownership(self) -> Self:
        if set(self.source_documents) != set(self.expected):
            raise ValueError("oracle source documents must cover every canonical scenario")
        for name, scenario in self.scenarios.items():
            code_map = self.expected[name]
            if set(self.source_documents[name]) != set(scenario.sources):
                raise ValueError("oracle source documents must exactly cover their scenario sources")
            if not FixtureSourceOwnership(frozenset(scenario.sources)).accepts(
                code_map.dependency_graph, code_map.extraction.manifest
            ):
                raise ValueError("canonical dependency graph must reference exactly its owned scenario sources")
            for fact in scenario.facts:
                fact.read_expected(code_map)
        return self
