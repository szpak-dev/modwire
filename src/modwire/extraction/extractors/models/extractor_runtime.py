from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.values.models.value_model import ValueModel
from .extractor_resource import ExtractorResource


class ExtractorRuntime(ValueModel):
    order: int
    descriptor: ExtractorDescriptor
    capabilities: tuple[CapabilityCoverage, ...]
    file_extensions: tuple[str, ...]
    command: tuple[str, ...]
    version_arguments: tuple[str, ...]
    entrypoint: ExtractorResource
