from typing import Literal

from modwire.application import DependencyGraph

from ....fixture_model import FixtureModel
from ...values.names.identifier import Identifier
from ..scenario_kind import ScenarioKind
from .extraction import ScenarioExtractionDocument


class ScenarioCodeMapDocument(FixtureModel):
    kind: Literal[ScenarioKind.CODE_MAP]
    producer: Identifier
    extraction: ScenarioExtractionDocument
    dependency_graph: DependencyGraph
