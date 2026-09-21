import sys
from dataclasses import dataclass

from wireup import injectable

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
