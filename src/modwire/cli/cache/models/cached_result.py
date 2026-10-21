from pydantic import field_validator

from ....shared.values.models.value_model import ValueModel
from .cache_outcome import CacheOutcome
from .cache_stage import CacheStage
from .cache_validation_error import CacheValidationError
from .cache_violation import CacheViolation


class CachedResult[Result](ValueModel):
    """A cached operation value together with one outcome per applicable stage."""

    value: Result
    outcomes: tuple[CacheOutcome, ...]

    @field_validator("outcomes")
    @classmethod
    def _unique_non_empty_stages(cls, value: tuple[CacheOutcome, ...]) -> tuple[CacheOutcome, ...]:
        if not value:
            raise CacheValidationError(CacheViolation.MISSING_CACHE_OUTCOME, "cached result")
        stages = tuple(outcome.stage for outcome in value)
        if len(stages) != len(set(stages)):
            raise CacheValidationError(CacheViolation.DUPLICATE_CACHE_STAGE_OUTCOME, "cached result")
        return value

    def outcome(self, stage: CacheStage) -> CacheOutcome:
        """Return the outcome for one applicable cache stage."""

        for outcome in self.outcomes:
            if outcome.stage == stage:
                return outcome
        raise CacheValidationError(CacheViolation.INAPPLICABLE_CACHE_STAGE, stage)
