from pydantic import Field

from modwire.application import CodeMapProducer

from ....fixture_model import FixtureModel
from ...values.names.identifier import Identifier
from ...values.names.scenario_id import ScenarioId
from ...values.paths.document_path import RepositoryDocumentPath


class ScenarioCatalogDocument(FixtureModel):
    producers: dict[Identifier, CodeMapProducer] = Field(min_length=1)
    scenarios: dict[ScenarioId, RepositoryDocumentPath] = Field(min_length=1)
