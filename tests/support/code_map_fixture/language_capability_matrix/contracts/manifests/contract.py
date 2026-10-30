from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel
from ...values.paths.path import RepositoryPath
from .scenario import ManifestScenario
from .transition import ManifestTransition


class ManifestContract(FixtureModel):
    root: RepositoryPath
    scenarios: tuple[ManifestScenario, ...] = Field(min_length=1)
    transitions: tuple[ManifestTransition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        names = tuple(scenario.name for scenario in self.scenarios)
        sources = tuple(scenario.source.value for scenario in self.scenarios)
        if len(set(names)) != len(names):
            raise ValueError("manifest scenario names contain duplicates")
        if len(set(sources)) != len(sources):
            raise ValueError("manifest scenario sources contain duplicates")
        for scenario in self.scenarios:
            if scenario.source.value.parts[0] != scenario.name.value:
                raise ValueError("manifest source is outside its named scenario")
        for transition in self.transitions:
            if transition.before not in names or transition.after not in names:
                raise ValueError("manifest transition names an undeclared scenario")
            if transition.before == transition.after:
                raise ValueError("manifest transition must change scenario")
        return self
