import sys
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.capability_status import CapabilityStatus
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.code.models.fact_capability import FactCapability
from ....shared.code.models.identity import FileId, ModuleId
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.batch_output_format import BatchOutputFormat
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_runtime import ExtractorRuntime
from .semantics.policies.module_identity_policy import PythonModuleIdentityPolicy


@injectable(as_type=SourceExtractor, qualifier="python")
@dataclass(frozen=True)
class PythonExtractor(SourceExtractor):
    identities: PythonModuleIdentityPolicy

    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            order=0,
            descriptor=ExtractorDescriptor(
                id="modwire.python.ast",
                version="1",
                language="python",
                runtime="python",
            ),
            capabilities=(
                CapabilityCoverage(
                    capability=FactCapability.SOURCES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every included Python source is identified and hashed.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SYMBOLS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, abstract classes, functions, and values are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLABLES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Functions, methods, constructors, and lambdas are extracted.",
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
                        "Class and callable decorators and declared type annotations are extracted; "
                        "arbitrary annotations are not evaluated."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.MODIFIERS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Visibility intent, callable kind, and class property member kind are normalized.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ATTRIBUTES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation=(
                        "Class property identity, exact declared type, visibility, optionality, and member kind "
                        "are extracted."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.ASSIGNED_VALUES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation=(
                        "Ordered assignment evidence distinguishes calls, references, literals, unresolved "
                        "expressions, and declarations without an assigned value."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every declared Python base expression is recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DEPENDENCIES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Imports are normalized and resolved when targets are present.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SPANS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Callable spans are exact; other symbol facts expose line counts.",
                ),
            ),
            file_extensions=(".py",),
            command=(sys.executable,),
            version_arguments=("--version",),
            entrypoint=ExtractorResource(
                package="modwire.extraction.extractors.resources",
                path="python/script.py",
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(
            size=500,
            parallel_threshold=1000,
            parallel_size=1000,
            max_workers=4,
            output_format=BatchOutputFormat.JSON,
            planner="balanced",
        )

    def module_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ModuleId, ...]]:
        return self.identities.identities(files)
