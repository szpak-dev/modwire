from pydantic import Field

from modwire.application import DeclarationIdentity

from ...model import FixtureModel
from ..values import Identifier, RepositorySourcePath

type DeclarationIdentityKey = tuple[str, str, str, int]


def declaration_identity_key(identity: DeclarationIdentity) -> DeclarationIdentityKey:
    return (
        str(identity.source_id),
        identity.family.value,
        identity.qualified_name,
        identity.ordinal,
    )


class SourceIdentityProjection(FixtureModel):
    authored: RepositorySourcePath
    canonical: RepositorySourcePath


class DeclarationIdentityProjection(FixtureModel):
    authored: DeclarationIdentity
    canonical: DeclarationIdentity


class CallableIdentityProjection(FixtureModel):
    authored: DeclarationIdentity
    canonical: DeclarationIdentity


class ParameterNameProjection(FixtureModel):
    authored_callable: DeclarationIdentity
    authored: Identifier
    canonical_callable: DeclarationIdentity
    canonical: Identifier


class ProjectionMappings(FixtureModel):
    sources: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
    declarations: tuple[DeclarationIdentityProjection, ...]
    callables: tuple[CallableIdentityProjection, ...]
    parameters: tuple[ParameterNameProjection, ...]
