from typing import Literal

from ....values.models.value_model import ValueModel
from .inventory_location_kind import InventoryLocationKind


class InventoryScopeLocation(ValueModel):
    kind: Literal[InventoryLocationKind.SCOPE] = InventoryLocationKind.SCOPE
