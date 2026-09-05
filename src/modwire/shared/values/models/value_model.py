import json
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic_yaml import to_yaml_str


class ValueModel(BaseModel):
    """Strict public value model used across the Modwire ecosystem."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True, validate_default=True)

    def to_json(self, *, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_yaml(self) -> str:
        return to_yaml_str(self)

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(**kwargs)

    def pretty(self) -> str:
        return json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True)
