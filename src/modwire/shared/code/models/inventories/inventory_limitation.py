from pydantic import Field

from ....values.models.value_model import ValueModel
from .inventory_limitation_kind import InventoryLimitationKind
from .inventory_scope_location import InventoryScopeLocation
from .inventory_source_location import InventorySourceLocation


class InventoryLimitation(ValueModel):
    kind: InventoryLimitationKind
    location: InventoryScopeLocation | InventorySourceLocation = Field(discriminator="kind")
    description: str = Field(min_length=1, pattern=r"\S")
