import ast
from dataclasses import dataclass, field

from .....shared.code.models.inventories.inventory_limitation import InventoryLimitation


@dataclass
class PythonInventoryEvidence:
    declarations: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    functions: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    values: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    callable_values: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    anonymous_callables: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    exports: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    implicit_exports: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    unowned_properties: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
    methods: dict[ast.ClassDef, list[InventoryLimitation]] = field(
        default_factory=dict[ast.ClassDef, list[InventoryLimitation]]
    )
    properties: dict[ast.ClassDef, list[InventoryLimitation]] = field(
        default_factory=dict[ast.ClassDef, list[InventoryLimitation]]
    )
    unresolved_methods: list[InventoryLimitation] = field(default_factory=list[InventoryLimitation])
