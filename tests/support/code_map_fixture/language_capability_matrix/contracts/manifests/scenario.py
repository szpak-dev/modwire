from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel
from ...values.names.manifest_scenario_id import ManifestScenarioId
from ...values.paths.source_path import RepositorySourcePath
from .claim import ManifestClaim


class ManifestScenario(FixtureModel):
    name: ManifestScenarioId
    source: RepositorySourcePath
    facts_digest: str = Field(pattern="^[0-9a-f]{64}$", strict=True)
    claims: tuple[ManifestClaim, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_claims(self) -> Self:
        if not self.source.value.is_relative_to(self.name.value):
            raise ValueError("manifest source is outside its named scenario")
        if len(set(self.claims)) != len(self.claims):
            raise ValueError(f"{self.name.value} contains duplicate manifest claims")
        for claim in self.claims:
            observation = claim.observation.root
            if observation.kind == "source":
                if observation.relative_path.value != self.source.value.relative_to(self.name.value):
                    raise ValueError("manifest source claim differs from its scenario source")
        return self
