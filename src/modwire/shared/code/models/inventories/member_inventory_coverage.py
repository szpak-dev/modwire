from ..immutable_code_value import ImmutableCodeValue
from .inventory_coverage import InventoryCoverage


class MemberInventoryCoverage(ImmutableCodeValue):
    methods: InventoryCoverage
    abstract_methods: InventoryCoverage
    properties: InventoryCoverage
    signatures: InventoryCoverage
