from typing import Self

from pydantic import ValidationInfo, model_validator
from pydantic.dataclasses import dataclass

from ...values.models.value_model import ValueModel
from ...values.models.value_reuse import ValueReuse


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class ImmutableCodeRecord:
    @model_validator(mode="after")
    def reuse(self, info: ValidationInfo[ValueReuse[Self] | None]) -> Self:
        if info.context is None:
            return self
        return info.context.retain(self)
