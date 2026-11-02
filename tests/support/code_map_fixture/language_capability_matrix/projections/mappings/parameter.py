from modwire.application import DeclarationIdentity

from ....fixture_model import FixtureModel
from ...values.names.identifier import Identifier


class ParameterNameProjection(FixtureModel):
    authored_callable: DeclarationIdentity
    authored: Identifier
    canonical: Identifier
