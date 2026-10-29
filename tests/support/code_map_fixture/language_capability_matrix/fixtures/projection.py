from pydantic import Field

from modwire.application import DeclarationIdentity, FactCapability

from ...model import FixtureModel
from ..values import Identifier, RepositorySourcePath


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
    callable: DeclarationIdentity
    authored: Identifier
    canonical: Identifier


class ReferenceProjection(FixtureModel):
    sources: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
    declarations: tuple[DeclarationIdentityProjection, ...]
    callables: tuple[CallableIdentityProjection, ...]
    parameters: tuple[ParameterNameProjection, ...]
    compared_capabilities: tuple[FactCapability, ...] = Field(min_length=1)
    language_specific_capabilities: tuple[FactCapability, ...]
