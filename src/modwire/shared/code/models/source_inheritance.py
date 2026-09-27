from pydantic import Field

from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity


class SourceInheritance(ValueModel):
    source_declaration_id: DeclarationIdentity
    kind: str = Field(min_length=1)
    target_reference: str = Field(min_length=1)
