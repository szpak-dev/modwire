from typing import ClassVar, Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .code_map_producer import CodeMapProducer
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .dependency_graph import DependencyGraph
from .source_extraction import SourceExtraction


class CodeMap(ValueModel):
    model_config = ConfigDict(frozen=True)
    schema_version: ClassVar[int] = 10
    language: str
    producer: CodeMapProducer
    extraction: SourceExtraction
    dependency_graph: DependencyGraph

    @model_validator(mode="after")
    def validate_producer_language(self) -> Self:
        if self.language != self.producer.extractor.language:
            raise CodeValidationError(CodeViolation.INCONSISTENT_PRODUCER_LANGUAGE, self.language)
        return self
