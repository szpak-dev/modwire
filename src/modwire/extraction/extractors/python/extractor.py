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
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_resource_set import ExtractorResourceSet
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
            resources=ExtractorResourceSet(
                entrypoint=ExtractorResource(
                    package="modwire.extraction.extractors.resources",
                    path="python/script.py",
                ),
                identity_resources=tuple(
                    ExtractorResource(package="modwire.extraction.extractors.python", path=path)
                    for path in self.identity_resource_paths()
                )
                + (
                    ExtractorResource(
                        package="modwire.extraction.extractors.resources",
                        path="python/script.py",
                    ),
                ),
            ),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, output_format="json")

    def module_identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ModuleId, ...]]:
        return self.identities.identities(files)

    def identity_resource_paths(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                (
                    "extractor.py",
                    "pipeline/source_parser.py",
                    "traversal/observation_reader.py",
                    "traversal/breadth_first_visitor.py",
                    "traversal/depth_first_visitor.py",
                    "observations/source_observation.py",
                    "observations/class_candidate.py",
                    "observations/function_candidate.py",
                    "observations/value_candidate.py",
                    "observations/callable_candidate.py",
                    "observations/call_candidate.py",
                    "observations/call_observation.py",
                    "observations/import_candidate.py",
                    "observations/export_candidate.py",
                    "observations/property_candidate.py",
                    "observations/inheritance_candidate.py",
                    "observations/source_context.py",
                    "semantics/reader.py",
                    "semantics/catalog.py",
                    "semantics/contribution.py",
                    "semantics/callables/classifier.py",
                    "semantics/callables/constructor_rule.py",
                    "semantics/callables/type_method_rule.py",
                    "semantics/callables/static_method_rule.py",
                    "semantics/callables/instance_method_rule.py",
                    "semantics/callables/function_rule.py",
                    "semantics/classes/classifier.py",
                    "semantics/classes/abstract_rule.py",
                    "semantics/classes/concrete_rule.py",
                    "semantics/exports/classifier.py",
                    "semantics/exports/explicit_rule.py",
                    "semantics/exports/implicit_rule.py",
                    "semantics/properties/classifier.py",
                    "semantics/properties/annotated_class_rule.py",
                    "semantics/properties/assigned_class_rule.py",
                    "semantics/properties/annotated_instance_rule.py",
                    "semantics/properties/assigned_instance_rule.py",
                    "semantics/calls/classifier.py",
                    "semantics/calls/qualified_target_rule.py",
                    "semantics/calls/local_target_rule.py",
                    "semantics/calls/instance_target_rule.py",
                    "semantics/calls/constructor_target_rule.py",
                    "semantics/calls/unresolved_target_rule.py",
                    "semantics/calls/dynamic_target_rule.py",
                    "semantics/policies/visibility_policy.py",
                    "semantics/policies/import_path_policy.py",
                    "semantics/policies/module_identity_policy.py",
                    "semantics/policies/declaration_identity_factory.py",
                    "semantics/policies/type_alias_classifier.py",
                    "semantics/policies/assigned_value_reader.py",
                    "semantics/policies/annotation_reader.py",
                    "semantics/policies/parameter_reader.py",
                    "semantics/policies/expression_reference_reader.py",
                    "semantics/contributors/class_contributor.py",
                    "semantics/contributors/function_contributor.py",
                    "semantics/contributors/value_contributor.py",
                    "semantics/contributors/callable_contributor.py",
                    "semantics/contributors/property_contributor.py",
                    "semantics/contributors/call_contributor.py",
                    "semantics/contributors/import_contributor.py",
                    "semantics/contributors/export_contributor.py",
                    "semantics/contributors/inheritance_contributor.py",
                    "semantics/contributors/metric_contributor.py",
                    "source_facts/reader.py",
                    "source_facts/contribution.py",
                    "source_facts/class_contributor.py",
                    "source_facts/function_contributor.py",
                    "source_facts/value_contributor.py",
                    "source_facts/callable_contributor.py",
                    "source_facts/property_contributor.py",
                    "source_facts/call_contributor.py",
                    "source_facts/import_contributor.py",
                    "source_facts/export_contributor.py",
                    "source_facts/inheritance_contributor.py",
                    "source_facts/metric_contributor.py",
                )
            )
        )
