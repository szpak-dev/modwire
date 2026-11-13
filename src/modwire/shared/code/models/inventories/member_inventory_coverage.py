from ....values.models.value_model import ValueModel
from .inventory_coverage import InventoryCoverage


class MemberInventoryCoverage(ValueModel):
    methods: InventoryCoverage
    abstract_methods: InventoryCoverage
    properties: InventoryCoverage
    signatures: InventoryCoverage
