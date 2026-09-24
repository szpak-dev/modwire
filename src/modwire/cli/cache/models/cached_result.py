from pydantic import field_validator

from ....shared.values.models.value_model import ValueModel
from .cache_outcome import CacheOutcome
from .cache_stage import CacheStage


class CachedResult[Result](ValueModel):
    """A cached operation value together with one outcome per applicable stage."""

    value: Result
    outcomes: tuple[CacheOutcome, ...]

    @field_validator("outcomes")
    @classmethod
    def _unique_non_empty_stages(cls, value: tuple[CacheOutcome, ...]) -> tuple[CacheOutcome, ...]:
        if not value:
            raise ValueError("A cached result requires at least one cache outcome.")
        stages = tuple(outcome.stage for outcome in value)
        if len(stages) != len(set(stages)):
            raise ValueError("A cached result must contain at most one outcome per stage.")
        return value

    def outcome(self, stage: CacheStage) -> CacheOutcome:
        """Return the outcome for one applicable cache stage."""

        for outcome in self.outcomes:
            if outcome.stage == stage:
                return outcome
        raise LookupError(f"Cache stage is not applicable to this result: {stage}")
