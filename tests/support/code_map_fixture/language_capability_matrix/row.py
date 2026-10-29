from modwire.application import FactCapability, RelationshipFamily

from ..language_convention import FixtureLanguageConvention
from ..model import FixtureModel
from .expectations.capability import CapabilityExpectation
from .expectations.fixtures import LanguageFixtureInventory
from .expectations.manifest import ManifestEvidenceExpectation
from .expectations.parameter_kind import ParameterKindExpectation
from .expectations.relationship import RelationshipExpectation
from .expectations.scenario import LimitationScenarioExpectation
from .limits.capability.limits import LanguageCapabilityLimitations
from .limits.relationship.limits import LanguageRelationshipLimitations


class LanguageCapabilityRow(FixtureModel):
    convention: FixtureLanguageConvention
    fixtures: LanguageFixtureInventory
    capabilities: dict[FactCapability, CapabilityExpectation]
    relationships: dict[RelationshipFamily, RelationshipExpectation]
    scenarios: tuple[LimitationScenarioExpectation, ...]
    parameter_kinds: ParameterKindExpectation
    manifest_expectations: dict[str, ManifestEvidenceExpectation]
    capability_limitations: LanguageCapabilityLimitations
    relationship_limitations: LanguageRelationshipLimitations
