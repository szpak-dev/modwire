from pydantic import Field

from modwire.application import SourceAssignedValueKind

from ....model import FixtureModel


class AssignedValueLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
    expected_value_kinds: dict[str, tuple[SourceAssignedValueKind, ...]]
