from pydantic import Field

from ....values.models.value_model import ValueModel
from ..sources.identity import FileId
from .declaration_family import DeclarationFamily


class DeclarationIdentity(ValueModel):
    source_id: FileId
    family: DeclarationFamily
    qualified_name: str = Field(min_length=1)
    ordinal: int = Field(ge=1)

    def canonical(self) -> str:
        """Return the stable source-qualified declaration identity."""

        return f"{self.source_id}::{self.family.value}:{self.ordinal}:{self.qualified_name}"
