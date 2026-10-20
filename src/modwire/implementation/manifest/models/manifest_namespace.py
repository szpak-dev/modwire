from ....shared.code.models.source_namespace_kind import SourceNamespaceKind
from ....shared.values.models.value_model import ValueModel


class ManifestNamespace(ValueModel):
    kind: SourceNamespaceKind
    qualified_name: str
