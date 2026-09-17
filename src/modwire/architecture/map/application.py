from dataclasses import dataclass

from wireup import injectable

from ...shared.code.models.queryable_code_map import QueryableCodeMap
from ..config.models.boundaries_config import BoundariesConfig
from .domain import ArchitectureMapper
from .models.architecture_map import ArchitectureMap


@injectable
@dataclass(frozen=True)
class MapApplication:
    mapper: ArchitectureMapper

    def load(self, code_map: QueryableCodeMap, config: BoundariesConfig) -> ArchitectureMap:
        return self.mapper.load(code_map, config)
