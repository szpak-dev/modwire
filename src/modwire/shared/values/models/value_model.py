import json
from collections.abc import Callable
from typing import Any, cast

import pydantic_yaml
from pydantic import BaseModel, ConfigDict


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True, validate_default=True)

    def to_json(self, *, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_yaml(self) -> str:
        render = cast(Callable[[BaseModel], str], getattr(pydantic_yaml, "to_yaml_str"))
        return render(self)

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(**kwargs)

    def pretty(self) -> str:
        return json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True)
