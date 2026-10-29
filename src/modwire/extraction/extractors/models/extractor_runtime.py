from ....shared.code.models.capabilities.capability_coverage import CapabilityCoverage
from ....shared.code.models.capabilities.relationship_coverage import RelationshipCoverage
from ....shared.code.models.maps.extractor_descriptor import ExtractorDescriptor
from ....shared.values.models.value_model import ValueModel
from .entrypoints.extractor_entrypoint import ExtractorEntrypoint


class ExtractorRuntime(ValueModel):
    order: int
    descriptor: ExtractorDescriptor
    capabilities: tuple[CapabilityCoverage, ...]
    relationship_capabilities: tuple[RelationshipCoverage, ...]
    file_extensions: tuple[str, ...]
    command: tuple[str, ...]
    version_arguments: tuple[str, ...]
    entrypoint: ExtractorEntrypoint
