from ....shared.code.models.source_namespace_kind import SourceNamespaceKind
from ....shared.values.models.value_model import ValueModel


class ManifestNamespace(ValueModel):
    source_id: str
    name: str
    kind: SourceNamespaceKind
