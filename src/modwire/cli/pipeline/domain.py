from abc import ABC, abstractmethod

from ...extraction.extractors.models.extraction_request import ExtractionRequest
from ...extraction.extractors.models.extractor_runtime import ExtractorRuntime
from ...shared.code.models.identity import FileId
from ...shared.code.models.source_extraction import SourceExtraction
from ...shared.code.models.source_file import SourceFile
from ..cache.models.source_inventory import SourceInventory
from .models.report_pipeline_context import ReportPipelineContext
from .models.scan_policy import ScanPolicy


class ReportPipelineStep(ABC):
    @abstractmethod
    def should_process(self, context: ReportPipelineContext) -> bool: ...

    @abstractmethod
    def process(self, context: ReportPipelineContext) -> ReportPipelineContext: ...


class SourceReader(ABC):
    @abstractmethod
    def ensure_available(self, runtime: ExtractorRuntime) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        raise NotImplementedError

    @abstractmethod
    def inventory(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceInventory:
        raise NotImplementedError

    @abstractmethod
    def extract_entries(
        self, request: ExtractionRequest, inventory: SourceInventory, source_ids: tuple[FileId, ...]
    ) -> dict[FileId, SourceFile]:
        raise NotImplementedError

    @abstractmethod
    def extract_source(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceExtraction:
        raise NotImplementedError
