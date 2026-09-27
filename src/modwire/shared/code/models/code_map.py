from typing import ClassVar, Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .code_map_producer import CodeMapProducer
from .dependency_graph import DependencyGraph
from .source_extraction import SourceExtraction


class CodeMap(ValueModel):
    model_config = ConfigDict(frozen=True)
    schema_version: ClassVar[int] = 5
    language: str
    producer: CodeMapProducer
    extraction: SourceExtraction
    dependency_graph: DependencyGraph

    @model_validator(mode="after")
    def validate_producer_language(self) -> Self:
        if self.language != self.producer.extractor.language:
            raise ValueError("Code map language must match its extractor descriptor.")
        return self
