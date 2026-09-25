from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import ModuleId
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="typescript")
@dataclass(frozen=True)
class TypeScriptExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            language="typescript",
            order=1,
            file_extensions=(".ts", ".tsx", ".js", ".jsx"),
            command=("node",),
            resource=ExtractorResource(package="modwire.extraction.extractors.resources", path="typescript/script.js"),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, parallel_threshold=1000, parallel_size=500, max_workers=16, output_format="jsonl")

    def module_identities(self, source_file: SourceFile) -> tuple[ModuleId, ...]:
        return (source_file.module_id,)
