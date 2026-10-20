from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.capability_status import CapabilityStatus
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.code.models.fact_capability import FactCapability
from ....shared.code.models.identity import FileId, ImportIdentity
from ....shared.code.models.source_file import SourceFile
from ....shared.code.models.source_namespace_kind import SourceNamespaceKind
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.batch_output_format import BatchOutputFormat
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="java")
@dataclass(frozen=True)
class JavaExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            order=3,
            descriptor=ExtractorDescriptor(
                id="modwire.java.javaparser",
                version="1",
                language="java",
                runtime="java",
            ),
            capabilities=(
                CapabilityCoverage(
                    capability=FactCapability.SOURCES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every included Java source is identified and hashed.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SYMBOLS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, interfaces, records, enums, and annotation declarations are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLABLES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Constructors, methods, and annotation elements are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.PARAMETERS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Callable parameter order, kind, and exact declared type are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ANNOTATIONS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Declaration annotations and exact declared types are extracted without evaluation.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.MODIFIERS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Visibility, callable kind, and property member kind are normalized.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ATTRIBUTES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Fields, record components, enum constants, and annotation elements are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ASSIGNED_VALUES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="Java member assigned-value evidence is not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Declared extension and implementation relations are recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.NAMESPACES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Authored package declarations are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DECLARATION_KINDS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Java declaration forms publish exact shared declaration kinds.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.COMPOSITION,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Extension and implementation are extracted; permits relations are not yet emitted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DEPENDENCIES,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Exact imports resolve internally; wildcard and implicit dependencies remain unresolved."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.SPANS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Callable spans are exact; other declarations expose line counts.",
                ),
            ),
            file_extensions=(".java",),
            command=("java",),
            entrypoint_arguments=("-jar",),
            version_arguments=("--version",),
            entrypoint=ExtractorResource(
                package="modwire.extraction.extractors.resources",
                path="java/script.jar",
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(
            size=500,
            parallel_threshold=500,
            parallel_size=500,
            max_workers=16,
            output_format=BatchOutputFormat.JSON_LINES,
        )

    def import_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        return {file_id: self.file_import_identities(source_file) for file_id, source_file in files.items()}

    def file_import_identities(self, source_file: SourceFile) -> tuple[ImportIdentity, ...]:
        package = next(
            (
                namespace.qualified_name
                for namespace in source_file.namespaces
                if namespace.kind is SourceNamespaceKind.PACKAGE
            ),
            "",
        )
        identities = {source_file.import_identity}
        for declaration in source_file.declarations:
            name = declaration.name.replace(".", "/")
            identity = f"{package.replace('.', '/')}/{name}" if package else name
            identities.add(ImportIdentity(identity))
        return tuple(sorted(identities, key=str))
