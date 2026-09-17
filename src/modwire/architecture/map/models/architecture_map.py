from ....shared.code.models.queryable_code_map import QueryableCodeMap
from ....shared.values.models.value_model import ValueModel
from .architecture_realm import ArchitectureRealm
from .tag_map import TagMap


class ArchitectureMap(ValueModel):
    code_map: QueryableCodeMap
    tag_map: TagMap
    modules: dict[str, tuple[str, ...]]
    layers: dict[str, tuple[str, ...]]
    unknown_files: tuple[str, ...]
    realm: ArchitectureRealm

    def with_realm(self, realm: ArchitectureRealm) -> "ArchitectureMap":
        return self.model_copy(update={"realm": realm})
