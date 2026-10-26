from pydantic import Field

from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .identity import FileId
from .source_call_resolution import SourceCallResolution


class SourceCall(ValueModel):
    source_callable_id: DeclarationIdentity
    ordinal: int = Field(strict=True, ge=1)
    target_callable_id: DeclarationIdentity | None
    source_id: FileId
    line: int
    expression: str
    resolution: SourceCallResolution
    target_name: str

    def identity(self) -> str:
        return f"{self.source_callable_id.canonical()}::call:{self.ordinal}"
