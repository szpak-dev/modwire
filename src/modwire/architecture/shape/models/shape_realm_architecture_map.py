from ....shared.code.models.queryable_code_map import QueryableCodeMap
from ....shared.values.models.value_model import ValueModel


class ShapeRealmArchitectureMap(ValueModel):
    code_map: QueryableCodeMap
    shape_realm_name: str
    shape_realm_source_ids: frozenset[str]
