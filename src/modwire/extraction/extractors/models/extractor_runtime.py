from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.code.models.relationship_coverage import RelationshipCoverage
from ....shared.values.models.value_model import ValueModel
from .extractor_resource import ExtractorResource


class ExtractorRuntime(ValueModel):
    order: int
    descriptor: ExtractorDescriptor
    capabilities: tuple[CapabilityCoverage, ...]
    relationship_capabilities: tuple[RelationshipCoverage, ...]
    file_extensions: tuple[str, ...]
    command: tuple[str, ...]
    entrypoint_arguments: tuple[str, ...]
    version_arguments: tuple[str, ...]
    entrypoint: ExtractorResource
