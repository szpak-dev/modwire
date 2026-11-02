from ..fixture_model import FixtureModel
from .contracts.coverage.contract import LanguageContract
from .oracle.binding import LanguageScenarioBinding
from .projections.reference_projection import ReferenceProjection


class LanguageCapabilityBundle(FixtureModel):
    contract: LanguageContract
    reference_projection: ReferenceProjection
    scenarios: tuple[LanguageScenarioBinding, ...]
