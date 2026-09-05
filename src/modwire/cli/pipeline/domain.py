from abc import ABC, abstractmethod

from modwire.cli.pipeline.models.report_pipeline_context import ReportPipelineContext
from modwire.extraction.extractors.models.extraction_request import ExtractionRequest
from modwire.extraction.extractors.models.extractor_runtime import ExtractorRuntime
from modwire.shared.code.models.source_extraction import SourceExtraction


class ReportPipelineStep(ABC):
    """Define one conditional rendering step for architecture reports."""

    @abstractmethod
    def should_process(self, context: ReportPipelineContext) -> bool: ...

    @abstractmethod
    def process(self, context: ReportPipelineContext) -> ReportPipelineContext: ...


class SourceReader(ABC):
    @abstractmethod
    def ensure_available(self, runtime: ExtractorRuntime) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_source_files(self, request: ExtractionRequest) -> bool:
        raise NotImplementedError

    @abstractmethod
    def extract_source(self, request: ExtractionRequest) -> SourceExtraction:
        raise NotImplementedError
