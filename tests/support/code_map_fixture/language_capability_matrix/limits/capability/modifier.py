from pydantic import Field

from modwire.application import SourceMemberKind

from ....model import FixtureModel


class ModifierLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_visibility_intents: tuple[str, ...]
    present_callable_kinds: tuple[str, ...]
    present_member_kinds: tuple[SourceMemberKind, ...]
    unrepresented_authored_modifiers: tuple[str, ...]
