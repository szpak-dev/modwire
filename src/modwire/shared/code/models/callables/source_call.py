from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

from ....values.models.string_reference import StringReference
from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from ..declarations.declaration_identity import DeclarationIdentity
from ..sources.identity import FileId
from .source_call_resolution import SourceCallResolution


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourceCall:
    source_callable_id: Annotated[DeclarationIdentity, ValueReference()]
    ordinal: int = Field(strict=True, ge=1)
    target_callable_id: Annotated[DeclarationIdentity, ValueReference()] | None
    source_id: Annotated[FileId, StringReference()]
    line: int
    expression: str
    resolution: SourceCallResolution
    target_name: str

    def identity(self) -> str:
        return f"{self.source_callable_id.canonical()}::call:{self.ordinal}"
