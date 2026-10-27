from pydantic import Field

from modwire.application import DeclarationIdentity

from ....model import FixtureModel


class SpanLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_exact_span_owners: tuple[DeclarationIdentity, ...]
    absent_exact_span_owners: tuple[DeclarationIdentity, ...]
