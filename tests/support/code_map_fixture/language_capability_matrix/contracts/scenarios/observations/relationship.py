from typing import Annotated

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .attribute import AttributeObservation
from .declaration_relation import DeclarationRelationObservation
from .dependency import DependencyObservation


class RelationshipObservation(
    FixtureRootModel[
        Annotated[
            DeclarationRelationObservation | AttributeObservation | DependencyObservation, Field(discriminator="kind")
        ]
    ]
):
    pass
