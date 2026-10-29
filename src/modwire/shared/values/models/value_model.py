import json

from pydantic import BaseModel, ConfigDict, TypeAdapter


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True, validate_default=True)

    def to_json(self, *, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_yaml(self) -> str:
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict[str, object]:
        return TypeAdapter(dict[str, object]).validate_json(self.model_dump_json())

    def pretty(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
