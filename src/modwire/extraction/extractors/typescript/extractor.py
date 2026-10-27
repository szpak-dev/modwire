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


@injectable(as_type=SourceExtractor, qualifier="typescript")
@dataclass(frozen=True)
class TypeScriptExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            order=1,
            descriptor=ExtractorDescriptor(
                id="modwire.typescript.ts-morph",
                version="2",
                language="typescript",
                runtime="node",
            ),
            capabilities=(
                CapabilityCoverage(
                    capability=FactCapability.SOURCES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every included TypeScript or JavaScript source is identified and hashed.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SYMBOLS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, interfaces, types, functions, and values are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLABLES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Functions, methods, constructors, and callable values are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation=(
                        "Static calls owned by extracted callables are emitted with explicit resolved, external, "
                        "unresolved, or dynamic state."
                    ),
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
                        "Class decorator expressions and declared type annotations are extracted; "
                        "decorators on other declarations are not yet emitted."
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
                        "Class and type property identity, exact declared type, visibility, optionality, and "
                        "member kind are extracted."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.ASSIGNED_VALUES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="TypeScript property assigned-value evidence is not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Class and interface heritage clauses are recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.NAMESPACES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="TypeScript namespace declarations are not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DECLARATION_KINDS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Classes, interfaces, and type aliases publish exact shared declaration kinds.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.COMPOSITION,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Extension and implementation heritage is extracted.",
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
            relationship_capabilities=(
                RelationshipCoverage(
                    family=RelationshipFamily.DECLARATION,
                    evidence_requirements=RelationshipFamily.DECLARATION.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Authored extension and implementation heritage is preserved without resolving "
                        "runtime base aliases."
                    ),
                    inventory=CapabilityStatus.SUPPORTED,
                    inventory_explanation=(
                        "Every authored class and interface heritage clause in included TypeScript sources "
                        "is emitted deterministically."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.MEMBER,
                    evidence_requirements=RelationshipFamily.MEMBER.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Declared member and callable types and static calls are preserved without resolving "
                        "runtime types or framework ownership."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Declared type and static-call evidence is emitted, but assigned-value relationship "
                        "evidence is not available."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.DEPENDENCY,
                    evidence_requirements=RelationshipFamily.DEPENDENCY.evidence_requirements,
                    semantics=CapabilityStatus.SUPPORTED,
                    semantics_explanation=(
                        "Authored import dependencies are normalized with explicit resolution state; "
                        "dynamic loading is excluded."
                    ),
                    inventory=CapabilityStatus.SUPPORTED,
                    inventory_explanation=(
                        "Every authored import declaration in included TypeScript and JavaScript sources is "
                        "emitted deterministically."
                    ),
                ),
            ),
            file_extensions=(".ts", ".tsx", ".js", ".jsx"),
            command=("node",),
            entrypoint_arguments=(),
            version_arguments=("--version",),
            entrypoint=ExtractorResource(
                package="modwire.extraction.extractors.resources",
                path="typescript/script.js",
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(
            size=500,
            parallel_threshold=1000,
            parallel_size=500,
            max_workers=16,
            output_format=BatchOutputFormat.JSON_LINES,
        )

    def import_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        return {file_id: (source_file.import_identity,) for file_id, source_file in files.items()}
