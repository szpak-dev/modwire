from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

from ....values.models.string_reference import StringReference
from ....values.models.value_model import ValueModel
from ..immutable_code_record import ImmutableCodeRecord
from ..sources.identity import FileId
from .declaration_family import DeclarationFamily


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class DeclarationIdentity(ImmutableCodeRecord):
    source_id: Annotated[FileId, StringReference()]
    family: DeclarationFamily
    qualified_name: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    content_digest: Annotated[str, StringReference()] = Field(pattern=r"^[0-9a-f]{64}$")

    def __hash__(self) -> int:
        return hash(self.source_id) ^ self.ordinal

    def canonical(self) -> str:
        """Return the identity of a declaration in one exact source capture."""

        return f"{self.source_id}@{self.content_digest}::{self.family}:{self.ordinal}:{self.qualified_name}"
