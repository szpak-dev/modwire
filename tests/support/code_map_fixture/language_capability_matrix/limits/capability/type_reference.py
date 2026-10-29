from pydantic import Field

from ....model import FixtureModel


class TypeReferenceLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_reference_names: tuple[str, ...]
    present_nested_reference_names: tuple[str, ...]
    absent_slot_count: int = Field(ge=0)
    unsupported_slot_count: int = Field(ge=0)
