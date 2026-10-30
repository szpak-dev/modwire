from modwire.application import DependencyGraph

from ....fixture_model import FixtureModel
from ...values.names.identifier import Identifier
from .extraction import ScenarioExtractionDocument


class ScenarioCodeMapDocument(FixtureModel):
    producer: Identifier
    extraction: ScenarioExtractionDocument
    dependency_graph: DependencyGraph
