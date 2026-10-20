from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.capability_coverage import CapabilityCoverage
from ....shared.code.models.capability_status import CapabilityStatus
from ....shared.code.models.extractor_descriptor import ExtractorDescriptor
from ....shared.code.models.fact_capability import FactCapability
from ....shared.code.models.identity import FileId, ImportIdentity
from ....shared.code.models.relationship_coverage import RelationshipCoverage
from ....shared.code.models.relationship_family import RelationshipFamily
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.batch_output_format import BatchOutputFormat
from ..models.extractor_resource import ExtractorResource
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
                version="2",
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
                    capability=FactCapability.ASSIGNED_VALUES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="PHP property assigned-value evidence is not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Class and interface inheritance declarations are recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.NAMESPACES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="PHP namespace declarations are not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DECLARATION_KINDS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, abstract classes, and interfaces publish exact shared declaration kinds.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.COMPOSITION,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Extension and implementation are extracted; trait use is not classified.",
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
            relationship_capabilities=(
                RelationshipCoverage(
                    family=RelationshipFamily.DECLARATION,
                    evidence_requirements=RelationshipFamily.DECLARATION.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Authored extension and implementation relations are preserved without classifying "
                        "trait use or framework conventions."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Class and interface heritage is emitted, but trait-use relationships are not yet classified."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.MEMBER,
                    evidence_requirements=RelationshipFamily.MEMBER.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Declared property and callable types are preserved without resolving runtime types "
                        "or framework ownership."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Declared type evidence is emitted, but assigned-value relationship evidence is not available."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.DEPENDENCY,
                    evidence_requirements=RelationshipFamily.DEPENDENCY.evidence_requirements,
                    semantics=CapabilityStatus.SUPPORTED,
                    semantics_explanation=(
                        "Authored namespace imports are normalized with explicit resolution state; dynamic "
                        "loading is excluded."
                    ),
                    inventory=CapabilityStatus.SUPPORTED,
                    inventory_explanation=(
                        "Every authored namespace import in included PHP sources is emitted deterministically."
                    ),
                ),
            ),
            file_extensions=(".php",),
            command=("php",),
            entrypoint_arguments=(),
            version_arguments=("--version",),
            entrypoint=ExtractorResource(
                package="modwire.extraction.extractors.resources",
                path="php/script.php",
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
        return {file_id: (source_file.import_identity,) for file_id, source_file in files.items()}
