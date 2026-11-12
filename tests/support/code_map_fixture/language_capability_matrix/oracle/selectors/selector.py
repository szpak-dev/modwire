from typing import Annotated

from pydantic import Field

from ....fixture_root_model import FixtureRootModel
from .dependencies import DependencySelector
from .source import SourceFileSelector


class ScenarioFactSelector(
    FixtureRootModel[Annotated[SourceFileSelector | DependencySelector, Field(discriminator="kind")]]
):
    pass
