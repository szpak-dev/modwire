from pydantic import ValidationInfo, model_validator

from ...values.models.value_model import ValueModel
from ...values.models.value_reuse import ValueReuse


class ImmutableCodeValue(ValueModel):
    @model_validator(mode="after")
    def reuse(self, info: ValidationInfo[ValueReuse["ImmutableCodeValue"] | None]) -> "ImmutableCodeValue":
        if info.context is None:
            return self
        return info.context.values.setdefault(self, self)
