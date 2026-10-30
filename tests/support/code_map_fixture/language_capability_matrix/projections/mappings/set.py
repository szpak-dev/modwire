from pydantic import Field

from ....fixture_model import FixtureModel
from .callable import CallableIdentityProjection
from .declaration import DeclarationIdentityProjection
from .parameter import ParameterNameProjection
from .source import SourceIdentityProjection


class ProjectionMappings(FixtureModel):
    sources: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
    declarations: tuple[DeclarationIdentityProjection, ...]
    callables: tuple[CallableIdentityProjection, ...]
    parameters: tuple[ParameterNameProjection, ...]
