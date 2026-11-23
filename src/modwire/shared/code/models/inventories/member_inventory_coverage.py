from typing import Annotated

from ....values.models.value_reference import ValueReference
from ..immutable_code_value import ImmutableCodeValue
from .inventory_coverage import InventoryCoverage


class MemberInventoryCoverage(ImmutableCodeValue):
    methods: Annotated[InventoryCoverage, ValueReference()]
    abstract_methods: Annotated[InventoryCoverage, ValueReference()]
    properties: Annotated[InventoryCoverage, ValueReference()]
    signatures: Annotated[InventoryCoverage, ValueReference()]
