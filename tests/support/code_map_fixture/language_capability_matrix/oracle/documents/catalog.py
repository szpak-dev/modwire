from pydantic import Field

from modwire.application import CodeMapProducer

from ....conclusion import Conclusion
from ....fixture_model import FixtureModel
from ...values.names.identifier import Identifier
from ...values.names.scenario_id import ScenarioId
from ...values.paths.document_path import RepositoryDocumentPath
from ..model_gap import ModelGapExpectation
from .extraction_obligation import ExtractionObligation


class ScenarioCatalogDocument(FixtureModel):
    producers: dict[Identifier, CodeMapProducer] = Field(min_length=1)
    scenarios: dict[ScenarioId, RepositoryDocumentPath] = Field(min_length=1)
    obligations: dict[Conclusion, ExtractionObligation]
    model_gaps: dict[Identifier, ModelGapExpectation]
    reviewed_gaps: dict[str, str]
