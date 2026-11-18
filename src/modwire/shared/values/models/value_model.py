import json
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationInfo, model_validator

from .value_reuse import ValueReuse


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True, validate_default=True)

    @model_validator(mode="after")
    def reuse_fields(self, info: ValidationInfo[ValueReuse[object] | None]) -> Self:
        if info.context is not None:
            self.__pydantic_fields_set__ = info.context.field_names(self.__pydantic_fields_set__)
            if "field_names_isolated" in self.__dict__:
                del self.field_names_isolated
        return self

    @cached_property
    def field_names_isolated(self) -> bool:
        self.__pydantic_fields_set__ = self.__pydantic_fields_set__.copy()
        return True

    @property
    def model_fields_set(self) -> set[str]:
        _ = self.field_names_isolated
        return self.__pydantic_fields_set__

    def to_json(self, *, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_yaml(self) -> str:
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict[str, object]:
        return TypeAdapter(dict[str, object]).validate_json(self.model_dump_json())

    def pretty(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
