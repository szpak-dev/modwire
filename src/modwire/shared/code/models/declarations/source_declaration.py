from typing import Self

from pydantic import Field, model_validator

from ..callables.source_class_method import SourceClassMethod
from ..callables.source_signature import SourceSignature
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..inventories.member_inventory_coverage import MemberInventoryCoverage
from ..values.source_class_property import SourceClassProperty
from .declaration_identity import DeclarationIdentity
from .source_placement import SourcePlacement
from .source_symbol import SourceSymbol
from .source_symbol_kind import SourceSymbolKind


class SourceDeclaration(SourceSymbol):
    declaration_id: DeclarationIdentity
    kind: SourceSymbolKind
    placement: SourcePlacement
    inventory: MemberInventoryCoverage
    methods: tuple[SourceClassMethod, ...] = Field(default_factory=tuple)
    abstract_methods: tuple[SourceClassMethod, ...] = Field(default_factory=tuple)
    properties: tuple[SourceClassProperty, ...] = Field(default_factory=tuple)
    signatures: tuple[SourceSignature, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        members = (*self.methods, *self.abstract_methods, *self.properties)
        if any(item.owner_declaration_id != self.declaration_id for item in members):
            raise CodeValidationError(CodeViolation.INCONSISTENT_MEMBER_OWNER, self.name)
        identities = tuple(item.declaration_id.canonical() for item in members)
        if len(identities) != len(set(identities)):
            raise CodeValidationError(CodeViolation.DUPLICATE_MEMBER_IDENTITY, self.name)
        return self

    @model_validator(mode="after")
    def validate_inventory(self) -> Self:
        self.inventory.methods.validate_item_count(len(self.methods))
        self.inventory.abstract_methods.validate_item_count(len(self.abstract_methods))
        self.inventory.properties.validate_item_count(len(self.properties))
        self.inventory.signatures.validate_item_count(len(self.signatures))
        return self
