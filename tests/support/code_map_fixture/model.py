from pydantic import BaseModel, ConfigDict, RootModel


class FixtureModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FixtureRootModel[FixtureValue](RootModel[FixtureValue]):
    model_config = ConfigDict(frozen=True)
