from typing import Annotated

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from .inventory_coverage import InventoryCoverage


class FileInventoryCoverage(ValueModel):
    declarations: Annotated[InventoryCoverage, ValueReference()]
    functions: Annotated[InventoryCoverage, ValueReference()]
    values: Annotated[InventoryCoverage, ValueReference()]
    callable_values: Annotated[InventoryCoverage, ValueReference()]
    anonymous_callables: Annotated[InventoryCoverage, ValueReference()]
    namespaces: Annotated[InventoryCoverage, ValueReference()]
    exports: Annotated[InventoryCoverage, ValueReference()]
    unresolved_methods: Annotated[InventoryCoverage, ValueReference()]
