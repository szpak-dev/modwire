from typing import Literal

from pydantic import Field

from ....values.models.value_model import ValueModel
from .absent import SourceTypeAbsent
from .kind import SourceTypeKind
from .unsupported import SourceTypeUnsupported


class SourceTypeReference(ValueModel):
    kind: Literal[SourceTypeKind.REFERENCE] = SourceTypeKind.REFERENCE
    name: str = Field(min_length=1)
    arguments: tuple["SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported", ...] = ()
