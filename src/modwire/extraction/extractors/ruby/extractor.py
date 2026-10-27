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


@injectable(as_type=SourceExtractor, qualifier="ruby")
@dataclass(frozen=True)
class RubyExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            order=4,
            descriptor=ExtractorDescriptor(
                id="modwire.ruby.prism",
                version="1",
                language="ruby",
                runtime="ruby",
            ),
            capabilities=(
                CapabilityCoverage(
                    capability=FactCapability.SOURCES,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Every included Ruby source is identified and hashed.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.SYMBOLS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Classes, modules, and statically named constants are extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLABLES,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Instance methods, singleton methods, and constructors owned by statically named classes "
                        "or modules are extracted; aliases and generated methods are not."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.CALLS,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Calls owned by extracted methods are emitted; dynamic dispatch and runtime-generated "
                        "targets remain unresolved."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.PARAMETERS,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Positional, keyword, rest, keyword-rest, block, and forwarding parameters are normalized."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.ANNOTATIONS,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="Ruby source annotations are not inferred.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.MODIFIERS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Authored method visibility and callable kind are normalized.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ATTRIBUTES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="Ruby instance, class, and generated attributes are not extracted.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.ASSIGNED_VALUES,
                    status=CapabilityStatus.UNSUPPORTED,
                    explanation="Ruby assigned-value relationship evidence is not extracted yet.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.INHERITANCE,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Authored class superclass clauses are recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.NAMESPACES,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Statically named module declarations are extracted as namespaces.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DECLARATION_KINDS,
                    status=CapabilityStatus.SUPPORTED,
                    explanation="Ruby classes, modules, and constants publish exact shared declaration kinds.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.COMPOSITION,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Literal include, prepend, and extend composition is recorded.",
                ),
                CapabilityCoverage(
                    capability=FactCapability.DEPENDENCIES,
                    status=CapabilityStatus.PARTIAL,
                    explanation=(
                        "Literal require and require_relative dependencies are normalized without load-path or "
                        "framework inference."
                    ),
                ),
                CapabilityCoverage(
                    capability=FactCapability.SPANS,
                    status=CapabilityStatus.PARTIAL,
                    explanation="Callable spans are exact; other declarations expose line counts.",
                ),
            ),
            relationship_capabilities=(
                RelationshipCoverage(
                    family=RelationshipFamily.DECLARATION,
                    evidence_requirements=RelationshipFamily.DECLARATION.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Authored superclass and literal module-composition relations are preserved without "
                        "refinements, metaprogramming, or framework inference."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Superclass, include, prepend, and extend sites are emitted, while dynamic composition "
                        "and reopened-definition merging are not available."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.MEMBER,
                    evidence_requirements=RelationshipFamily.MEMBER.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Authored methods and bounded same-file call targets are preserved without runtime "
                        "dispatch or generated members."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Declared method and static call evidence is emitted, but attributes and assigned-value "
                        "relationship evidence are not available."
                    ),
                ),
                RelationshipCoverage(
                    family=RelationshipFamily.DEPENDENCY,
                    evidence_requirements=RelationshipFamily.DEPENDENCY.evidence_requirements,
                    semantics=CapabilityStatus.PARTIAL,
                    semantics_explanation=(
                        "Literal require and require_relative calls are normalized without Ruby load-path, "
                        "Rails, or Zeitwerk inference."
                    ),
                    inventory=CapabilityStatus.PARTIAL,
                    inventory_explanation=(
                        "Authored literal loads are emitted, but dynamic loads and framework-generated "
                        "dependencies are not available."
                    ),
                ),
            ),
            file_extensions=(".rb",),
            command=("ruby",),
            entrypoint_arguments=(),
            version_arguments=(
                "-rprism",
                "-e",
                (
                    'abort "Ruby 4.0.x and Prism 1.9.x are required." unless '
                    'RUBY_VERSION.start_with?("4.0.") && Prism::VERSION.start_with?("1.9."); '
                    'print "ruby #{RUBY_VERSION}; prism #{Prism::VERSION}"'
                ),
            ),
            entrypoint=ExtractorResource(
                package="modwire.extraction.extractors.resources",
                path="ruby/script.rb",
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(
            size=500,
            parallel_threshold=500,
            parallel_size=500,
            max_workers=8,
            output_format=BatchOutputFormat.JSON_LINES,
        )

    def import_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        return {file_id: (source_file.import_identity,) for file_id, source_file in files.items()}
