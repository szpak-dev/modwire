from pydantic import BaseModel, ConfigDict


class FixtureModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
