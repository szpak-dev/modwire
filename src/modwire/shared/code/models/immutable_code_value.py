from typing import Self

from pydantic import ValidationInfo, model_validator

from ...values.models.value_model import ValueModel
from ...values.models.value_reuse import ValueReuse


class ImmutableCodeValue(ValueModel):
    @model_validator(mode="after")
    def reuse(self, info: ValidationInfo[ValueReuse[Self] | None]) -> Self:
        if info.context is None:
            return self
        retained = info.context.retain(self)
        if retained is self:
            return self.reuse_fields(info.context.field_names(self.__pydantic_fields_set__))
        return retained
