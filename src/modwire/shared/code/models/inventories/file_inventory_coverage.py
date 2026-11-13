from ....values.models.value_model import ValueModel
from .inventory_coverage import InventoryCoverage


class FileInventoryCoverage(ValueModel):
    declarations: InventoryCoverage
    functions: InventoryCoverage
    values: InventoryCoverage
    callable_values: InventoryCoverage
    anonymous_callables: InventoryCoverage
    namespaces: InventoryCoverage
    exports: InventoryCoverage
    unresolved_methods: InventoryCoverage
