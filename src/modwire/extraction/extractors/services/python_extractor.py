import sys
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import ModuleId
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="python")
@dataclass(frozen=True)
class PythonExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            language="python",
            order=0,
            file_extensions=(".py",),
            command=(sys.executable,),
            resource=ExtractorResource(package="modwire.extraction.extractors.resources", path="python/script.py"),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, output_format="json")

    def module_identities(self, source_file: SourceFile) -> tuple[ModuleId, ...]:
        module_id = source_file.module_id
        value = str(module_id)
        if value == "__init__" or not value.endswith("/__init__"):
            return (module_id,)
        return (module_id, ModuleId(value.rsplit("/", 1)[0]))
