from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import ModuleId
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceExtractor
from ..models.batch_config import BatchConfig
from ..models.extractor_resource import ExtractorResource
from ..models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="php")
@dataclass(frozen=True)
class PhpExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            language="php",
            order=2,
            file_extensions=(".php",),
            command=("php",),
            resource=ExtractorResource(package="modwire.extraction.extractors.resources", path="php/script.php"),
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, parallel_threshold=500, parallel_size=500, max_workers=16, output_format="jsonl")

    def module_identities(self, source_file: SourceFile) -> tuple[ModuleId, ...]:
        return (source_file.module_id,)
