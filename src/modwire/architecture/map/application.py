from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.application import ConfigApplication
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap

from .domain import ArchitectureMapper
from .models.architecture_map import ArchitectureMap


@injectable
@dataclass(frozen=True)
class MapApplication:
    mapper: ArchitectureMapper
    config: ConfigApplication

    def load(self, code_map: QueryableCodeMap) -> ArchitectureMap:
        return self.mapper.load(code_map, self.config.boundaries)
