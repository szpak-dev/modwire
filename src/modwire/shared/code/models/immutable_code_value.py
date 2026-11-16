from pydantic import ValidationInfo, model_validator

from ...values.models.value_model import ValueModel


class ImmutableCodeValue(ValueModel):
    @model_validator(mode="after")
    def reuse(
        self, info: ValidationInfo[dict["ImmutableCodeValue", "ImmutableCodeValue"] | None]
    ) -> "ImmutableCodeValue":
        if info.context is None:
            return self
        return info.context.setdefault(self, self)
