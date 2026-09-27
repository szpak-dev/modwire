from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.capability_status import CapabilityStatus
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.code.models.fact_capability import FactCapability
from ....shared.code.models.identity import ModuleId
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_resource_set import ExtractorResourceSet
from ..models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="php")
@dataclass(frozen=True)
class PhpExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            order=2,
            descriptor=ExtractorDescriptor(
                id="modwire.php.php-parser",
                version="1",
                language="php",
                runtime="php",
            ),
            capabilities=(
                CapabilityCoverage(
                    capability=FactCapability.SOURCES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every included PHP source is identified and hashed.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SYMBOLS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, interfaces, functions, and values are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLABLES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Functions, methods, constructors, closures, and arrow functions are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.PARAMETERS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Callable parameter order, kind, annotation, and default presence are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ANNOTATIONS,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Class and interface attributes and declared type annotations are extracted; "
                        "attributes on other declarations are not yet emitted."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.MODIFIERS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Visibility intent, callable kind, and property member kind are normalized.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ATTRIBUTES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation=(
                        "Declared and promoted property identity, exact declared type, visibility, optionality, "
                        "and member kind are extracted."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Class and interface inheritance declarations are recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DEPENDENCIES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Namespace imports are normalized and resolved when targets are present.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SPANS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Callable spans are exact; other symbol facts expose line counts.",
                ),
            ),
            file_extensions=(".php",),
            command=("php",),
            version_arguments=("--version",),
            resources=ExtractorResourceSet(
                entrypoint=ExtractorResource(
                    package="modwire.extraction.extractors.resources",
                    path="php/script.php",
                ),
                identity_resources=(
                    ExtractorResource(
                        package="modwire.extraction.extractors.resources",
                        path="php/script.php",
                    ),
                ),
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, parallel_threshold=500, parallel_size=500, max_workers=16, output_format="jsonl")

    def module_identities(self, source_file: SourceFile) -> tuple[ModuleId, ...]:
        return (source_file.module_id,)
