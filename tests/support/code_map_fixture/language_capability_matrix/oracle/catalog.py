from functools import cached_property
from typing import Self

from pydantic import Field, model_validator

from modwire.application import CodeMap, FileId, ScanPolicy

from ...conclusion import Conclusion
from ...fixture_model import FixtureModel
from ...scenario_contract_error import ScenarioContractError
from ...scenario_violation import ScenarioViolation
from ..values.names.identifier import Identifier
from ..values.names.scenario_id import ScenarioId
from ..values.paths.document_path import RepositoryDocumentPath
from .documents.extraction_obligation import ExtractionObligation
from .expected_scenario import ExpectedScenario
from .fact_selector_kind import FactSelectorKind
from .model_gap import ModelGapExpectation
from .ownership import FixtureSourceOwnership
from .reference import FixtureFactReference
from .scenario import CanonicalFixtureScenario
from .scenario_kind import ScenarioKind
from .selectors.dependencies import DependencySelector
from .selectors.selector import ScenarioFactSelector
from .selectors.source import SourceFileSelector


class FixtureScenarioCatalog(FixtureModel):
    expected: dict[ScenarioId, ExpectedScenario] = Field(min_length=1)
    source_documents: dict[ScenarioId, dict[FileId, RepositoryDocumentPath]]
    obligations: dict[Conclusion, ExtractionObligation]
    model_gaps: dict[Identifier, ModelGapExpectation]
    reviewed_gaps: dict[str, str]

    @cached_property
    def scenarios(self) -> dict[ScenarioId, CanonicalFixtureScenario]:
        return {
            name: CanonicalFixtureScenario(
                sources=tuple(self.source_documents[name]),
                facts=tuple(
                    FixtureFactReference(selector=ScenarioFactSelector(selector))
                    for source in self.source_documents[name]
                    for selector in (
                        SourceFileSelector(kind=FactSelectorKind.SOURCE_FILE, source=source),
                        *(
                            (DependencySelector(kind=FactSelectorKind.DEPENDENCIES, source=source),)
                            if expected.root.kind is ScenarioKind.CODE_MAP
                            else ()
                        ),
                    )
                ),
            )
            for name, expected in self.expected.items()
        }

    def code_map(self, scenario: ScenarioId) -> CodeMap:
        expected = self.expected[scenario].root
        if expected.kind is ScenarioKind.CODE_MAP:
            return expected.code_map
        raise ScenarioContractError(ScenarioViolation.EXPECTED_CODE_MAP, scenario.value)

    def policy(self, scenario: ScenarioId) -> ScanPolicy:
        expected = self.expected[scenario].root
        if expected.kind is ScenarioKind.CODE_MAP:
            return expected.code_map.extraction.manifest.policy
        return expected.policy

    @model_validator(mode="after")
    def validate_source_ownership(self) -> Self:
        if set(self.source_documents) != set(self.expected):
            raise ScenarioContractError(ScenarioViolation.SOURCE_DOCUMENTS, "scenario inventory")
        referenced_gaps: set[Identifier] = set()
        for name, scenario in self.scenarios.items():
            expected = self.expected[name].root
            if set(self.source_documents[name]) != set(scenario.sources):
                raise ScenarioContractError(ScenarioViolation.SOURCE_DOCUMENTS, name.value)
            if expected.kind is ScenarioKind.SOURCE_FACTS:
                if set(expected.sources) != set(scenario.sources):
                    raise ScenarioContractError(ScenarioViolation.SOURCE_OWNERSHIP, name.value)
                for source in expected.sources.values():
                    referenced_gaps.update(source.gaps)
                continue
            code_map = expected.code_map
            if not FixtureSourceOwnership(frozenset(scenario.sources)).accepts(
                code_map.dependency_graph, code_map.extraction.manifest
            ):
                raise ScenarioContractError(ScenarioViolation.SOURCE_OWNERSHIP, name.value)
            for fact in scenario.facts:
                fact.read_expected(code_map)
        if referenced_gaps != set(self.model_gaps):
            raise ScenarioContractError(ScenarioViolation.MODEL_GAP_REFERENCES, "unknown or unused model limitation")
        return self
