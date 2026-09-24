from typing import Literal

from pydantic import Field

from ....shared.values.models.value_model import ValueModel


class CacheStorageState(ValueModel):
    schema_version: Literal[1] = 1
    total_bytes: int = Field(ge=0)
    entry_count: int = Field(ge=0)
