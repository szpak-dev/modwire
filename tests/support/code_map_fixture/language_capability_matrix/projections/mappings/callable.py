from modwire.application import DeclarationIdentity

from ....fixture_model import FixtureModel


class CallableIdentityProjection(FixtureModel):
    authored: DeclarationIdentity
    canonical: DeclarationIdentity
