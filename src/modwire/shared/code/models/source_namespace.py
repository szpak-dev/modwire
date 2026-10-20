from pydantic import Field

from ...values.models.value_model import ValueModel
from .source_namespace_kind import SourceNamespaceKind


class SourceNamespace(ValueModel):
    kind: SourceNamespaceKind
    qualified_name: str = Field(min_length=1)
