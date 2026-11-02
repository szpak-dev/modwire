from typing import Self

from pydantic import model_validator

from ....shared.values.models.value_model import ValueModel
from .cache_outcome import CacheOutcome
from .cache_stage import CacheStage
from .cache_validation_error import CacheValidationError
from .cache_violation import CacheViolation


class CachedResult[Result](ValueModel):
    """A cached operation value together with one outcome per applicable stage."""

    value: Result
    outcomes: tuple[CacheOutcome, ...]

    @model_validator(mode="after")
    def validate_outcomes(self) -> Self:
        if not self.outcomes:
            raise CacheValidationError(CacheViolation.MISSING_CACHE_OUTCOME, "cached result")
        stages = tuple(outcome.stage for outcome in self.outcomes)
        if len(stages) != len(set(stages)):
            raise CacheValidationError(CacheViolation.DUPLICATE_CACHE_STAGE_OUTCOME, "cached result")
        return self

    def outcome(self, stage: CacheStage) -> CacheOutcome:
        """Return the outcome for one applicable cache stage."""

        for outcome in self.outcomes:
            if outcome.stage == stage:
                return outcome
        raise CacheValidationError(CacheViolation.INAPPLICABLE_CACHE_STAGE, stage)
