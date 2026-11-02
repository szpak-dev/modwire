from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel
from ...values.enums.manifest_change import ManifestChange
from ...values.names.manifest_scenario_id import ManifestScenarioId


class ManifestTransition(FixtureModel):
    before: ManifestScenarioId
    after: ManifestScenarioId
    changes: tuple[ManifestChange, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        if len(set(self.changes)) != len(self.changes):
            raise ValueError("manifest transition changes contain duplicates")
        return self
