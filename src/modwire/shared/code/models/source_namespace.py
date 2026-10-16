from pydantic import Field

from ...values.models.value_model import ValueModel
from .source_namespace_kind import SourceNamespaceKind


class SourceNamespace(ValueModel):
    name: str = Field(min_length=1)
    kind: SourceNamespaceKind
