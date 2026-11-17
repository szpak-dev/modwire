from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from ..sources.identity import FileId
from .declaration_family import DeclarationFamily


class DeclarationIdentity(ImmutableCodeValue):
    source_id: FileId
    family: DeclarationFamily
    qualified_name: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    def canonical(self) -> str:
        """Return the identity of a declaration in one exact source capture."""

        return f"{self.source_id}@{self.content_digest}::{self.family.value}:{self.ordinal}:{self.qualified_name}"
