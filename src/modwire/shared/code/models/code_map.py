from typing import ClassVar, Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .code_map_producer import CodeMapProducer
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .dependency_graph import DependencyGraph
from .source_call_resolution import SourceCallResolution
from .source_extraction import SourceExtraction


class CodeMap(ValueModel):
    model_config = ConfigDict(frozen=True)
    schema_version: ClassVar[int] = 11
    language: str
    producer: CodeMapProducer
    extraction: SourceExtraction
    dependency_graph: DependencyGraph

    @model_validator(mode="after")
    def validate_facts(self) -> Self:
        self.validate_producer_language()
        self.validate_resolved_call_targets()
        return self

    def validate_producer_language(self) -> None:
        if self.language != self.producer.extractor.language:
            raise CodeValidationError(CodeViolation.INCONSISTENT_PRODUCER_LANGUAGE, self.language)

    def validate_resolved_call_targets(self) -> None:
        callable_ids = {
            item.declaration_id.canonical()
            for source_file in self.extraction.files.values()
            for item in source_file.callables
        }
        if any(
            call.resolution is SourceCallResolution.RESOLVED
            and (call.target_callable_id is None or call.target_callable_id.canonical() not in callable_ids)
            for source_file in self.extraction.files.values()
            for call in source_file.calls
        ):
            raise CodeValidationError(CodeViolation.UNKNOWN_RESOLVED_CALL_TARGET, self.language)
