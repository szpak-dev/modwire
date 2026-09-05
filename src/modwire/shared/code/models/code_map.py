from typing import Any

from pydantic import ConfigDict

from ...values.models.value_model import ValueModel
from .dependency_graph import DependencyGraph
from .source_extraction import SourceExtraction


class CodeMap(ValueModel):
    model_config = ConfigDict(frozen=True)
    language: str
    extraction: SourceExtraction
    dependency_graph: DependencyGraph

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(**kwargs)

    def to_json(self, *, indent: int | None = None) -> str:
        return self.model_dump_json(indent=indent)
