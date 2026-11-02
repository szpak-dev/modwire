from modwire.application import DeclarationIdentity

from ....fixture_model import FixtureModel


class DeclarationIdentityProjection(FixtureModel):
    authored: DeclarationIdentity
    canonical: DeclarationIdentity
