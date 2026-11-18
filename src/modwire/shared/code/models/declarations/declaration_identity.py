from typing import Annotated, Self

from pydantic import Field, ValidationInfo, model_validator
from pydantic.dataclasses import dataclass

from ....values.models.string_reference import StringReference
from ....values.models.value_model import ValueModel
from ....values.models.value_reuse import ValueReuse
from ..sources.identity import FileId
from .declaration_family import DeclarationFamily


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class DeclarationIdentity:
    source_id: Annotated[FileId, StringReference()]
    family: DeclarationFamily
    qualified_name: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    content_digest: Annotated[str, StringReference()] = Field(pattern=r"^[0-9a-f]{64}$")

    def __hash__(self) -> int:
        return hash((self.source_id, self.ordinal))

    def canonical(self) -> str:
        """Return the identity of a declaration in one exact source capture."""

        return f"{self.source_id}@{self.content_digest}::{self.family}:{self.ordinal}:{self.qualified_name}"

    @model_validator(mode="after")
    def reuse(self, info: ValidationInfo[ValueReuse[Self] | None]) -> Self:
        if info.context is None:
            return self
        return info.context.retain(self)
