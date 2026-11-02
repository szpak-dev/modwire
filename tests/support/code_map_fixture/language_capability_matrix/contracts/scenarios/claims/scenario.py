from typing import Annotated, Self

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .capability import CapabilityClaim
from .relationship import RelationshipClaim


class ScenarioClaim(FixtureRootModel[Annotated[CapabilityClaim | RelationshipClaim, Field(discriminator="kind")]]):
    def same_fact(self, other: Self) -> bool:
        first = self.root
        second = other.root
        if first.kind == "capability" and second.kind == "capability":
            return (
                first.capability is second.capability
                and first.state is second.state
                and first.observation == second.observation
            )
        if first.kind == "relationship" and second.kind == "relationship":
            return (
                first.relationship is second.relationship
                and first.aspect is second.aspect
                and first.state is second.state
                and first.observation == second.observation
            )
        return False
