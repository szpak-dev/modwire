from dataclasses import dataclass

from wireup import injectable

from modwire.extraction.extractors.domain import SourceExtractor
from modwire.extraction.extractors.models.batch_config import BatchConfig
from modwire.extraction.extractors.models.extractor_runtime import ExtractorRuntime


@injectable(as_type=SourceExtractor, qualifier="php")
@dataclass(frozen=True)
class PhpExtractor(SourceExtractor):
    @property
    def runtime(self) -> ExtractorRuntime:
        return ExtractorRuntime(
            language="php", order=2, file_extensions=(".php",), command=("php",), resource="php/script.php"
        )

    @property
    def batch_config(self) -> BatchConfig:
        return BatchConfig(size=500, parallel_threshold=500, parallel_size=500, max_workers=16, output_format="jsonl")
