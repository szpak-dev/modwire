from pydantic import Field

from modwire.application import SourceAssignedValueKind

from ....model import FixtureModel


class MemberRelationshipLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
    present_value_kinds: tuple[SourceAssignedValueKind, ...]
    absent_value_kinds: tuple[SourceAssignedValueKind, ...]
