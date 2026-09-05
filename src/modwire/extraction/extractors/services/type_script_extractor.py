from dataclasses import dataclass

from wireup import injectable

from modwire.extraction.extractors.domain import SourceExtractor
from modwire.extraction.extractors.models.batch_config import BatchConfig
from modwire.extraction.extractors.models.extractor_runtime import ExtractorRuntime


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
            resource="typescript/script.js",
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, parallel_threshold=1000, parallel_size=500, max_workers=16, output_format="jsonl")
