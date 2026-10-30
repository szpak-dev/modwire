from pydantic import ConfigDict, RootModel


class FixtureRootModel[FixtureValue](RootModel[FixtureValue]):
    model_config = ConfigDict(frozen=True, strict=True)
