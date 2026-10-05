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


@injectable(as_type=SourceExtractor, qualifier="python")
@dataclass(frozen=True)
class PythonExtractor(SourceExtractor):
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
                identity_resources=(
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="assigned_value_reader.py",
                    ),
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="call_context.py",
                    ),
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="call_reader.py",
                    ),
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="domain.py",
                    ),
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="expression_reference_reader.py",
                    ),
                    ExtractorResource(
                        package="modwire.extraction.extractors.python",
                        path="syntax_parser.py",
                    ),
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
        package_modules = {
            str(source_file.module_id).removesuffix("/__init__")
            for source_file in files.values()
            if str(source_file.module_id).endswith("/__init__")
        }
        identities: dict[FileId, tuple[ModuleId, ...]] = {}
        for file_id, source_file in files.items():
            module_id = source_file.module_id
            value = str(module_id)
            candidates = [module_id]
            if value.endswith("/__init__"):
                candidates.append(ModuleId(value.rsplit("/", 1)[0]))
            parts = value.split("/")
            package_start = len(parts) - 1
            for index in range(len(parts) - 2, -1, -1):
                if "/".join(parts[: index + 1]) not in package_modules:
                    break
                package_start = index
            if package_start < len(parts) - 1:
                import_parts = parts[package_start:]
                if import_parts[-1] == "__init__":
                    import_parts = import_parts[:-1]
                if import_parts:
                    candidates.append(ModuleId("/".join(import_parts)))
            identities[file_id] = tuple(dict.fromkeys(candidates))
        return identities
